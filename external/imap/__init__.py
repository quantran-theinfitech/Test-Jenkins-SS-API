import email.utils as utils
import imaplib
import re
from datetime import datetime, timedelta

from external.mautic import LoggingDecorator
from utils.chunk_string import trim_email

from .schema.imap import IMAPBounceInfo


class IMAPService(LoggingDecorator):
    @classmethod
    def exclude_logging(cls):
        return ["__init__", "auth"]

    def auth(self, host: str, port: int, email: str, password: str):
        try:
            imap = imaplib.IMAP4_SSL(host, port)
            imap.login(email, password)
            return imap
        except Exception as e:
            raise Exception(f"IMAP Authentication failed: {e}")

    def check_bounced_email(
        self, host: str, port: int, email: str, password: str, since_date: datetime
    ):
        service = self.auth(host, port, email, password)
        service.select("INBOX")

        # Look for common mail daemon senders that typically send bounce notifications
        daemon_senders = [
            "FROM mailer-daemon",
            "FROM postmaster",
            "FROM daemon",
            "FROM mail-daemon",
            "FROM system",
            "FROM maildelivery",
            "FROM mail-delivery",
            "FROM mailerdaemon",
        ]

        # Format date according to IMAP RFC 3501 specification with time precision
        formatted_date = since_date.strftime("%d-%b-%Y")

        # Create search criteria using proper IMAP syntax
        search_criteria = f'SINCE "{formatted_date}"'

        # Execute search with proper syntax
        status, data = service.search(None, search_criteria)

        bounced_emails_info = []

        if data[0]:  # If we have messages in the date range
            # Then filter each daemon sender
            all_bounce_ids = []
            for sender in daemon_senders:
                status, sender_data = service.search(None, sender)
                if sender_data[0]:
                    all_bounce_ids.extend(sender_data[0].split())

            # Remove duplicates
            unique_bounce_ids = list(set(all_bounce_ids))

            # For minute-level precision, we need to filter messages by checking INTERNALDATE
            filtered_bounce_ids = []
            precise_timestamp = since_date.timestamp()

            for msg_id in unique_bounce_ids:
                # Get the internal date of the message
                status, date_data = service.fetch(msg_id, "(INTERNALDATE)")
                if status == "OK":
                    # Extract the date from the response
                    date_str = date_data[0].decode("utf-8")
                    # Parse the date and compare with our target time

                    # Extract date from INTERNALDATE response
                    date_match = re.search(r'INTERNALDATE "([^"]+)"', date_str)
                    if date_match:
                        try:
                            parsed_date = utils.parsedate_to_datetime(
                                date_match.group(1)
                            )
                            if (
                                parsed_date
                                and parsed_date.timestamp() >= precise_timestamp
                            ):
                                filtered_bounce_ids.append(msg_id)
                        except Exception:
                            # If we can't parse the date, include the message anyway
                            filtered_bounce_ids.append(msg_id)

            # Use filtered IDs instead of original unique_bounce_ids
            unique_bounce_ids = filtered_bounce_ids

            # Process each bounce email to extract relevant information
            for msg_id in unique_bounce_ids:
                # Fetch the email content
                status, msg_data = service.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                # Parse email headers
                email_headers = {}
                for part in msg_data:
                    if isinstance(part, tuple):
                        # Extract headers
                        header_lines = part[1].split(b"\r\n")
                        for line in header_lines:
                            if line and b":" in line:
                                try:
                                    key, value = line.decode(
                                        "utf-8", errors="ignore"
                                    ).split(":", 1)
                                    email_headers[key.strip().lower()] = value.strip()
                                except Exception:
                                    continue

                # Get the email body to extract bounce codes
                email_body = ""
                try:
                    for part in msg_data:
                        if isinstance(part, tuple):
                            # Try to extract the email body
                            body_parts = part[1].split(b"\r\n\r\n", 1)
                            if len(body_parts) > 1:
                                email_body = body_parts[1].decode(
                                    "utf-8", errors="ignore"
                                )
                                break
                except Exception:
                    email_body = ""

                # Extract relevant information
                bounce_info = IMAPBounceInfo(
                    message_id=email_headers.get("in-reply-to", ""),
                    references=email_headers.get("references", None),
                    subject=email_headers.get("subject", ""),
                    original_recipient=email_headers.get("original_recipient", ""),
                )

                # Try to extract the original recipient from the bounce message
                if "x-failed-recipients" in email_headers:
                    bounce_info.original_recipient = email_headers[
                        "x-failed-recipients"
                    ]

                # Extract bounce and diagnostic codes from the email body
                if email_body:
                    # Common patterns for bounce codes
                    bounce_patterns = [
                        "Status: (\\d\\.\\d\\.\\d)",
                        "Status code: (\\d\\.\\d\\.\\d)",
                        "Bounce code: (\\d\\.\\d\\.\\d)",
                        "SMTP error code: (\\d+)",
                    ]

                    # Common patterns for diagnostic codes
                    diag_patterns = [
                        "Diagnostic-Code: (.+)",
                        "Diagnostic: (.+)",
                        "Diagnostic code: (.+)",
                    ]

                    # Search for bounce codes
                    for pattern in bounce_patterns:
                        match = re.search(pattern, email_body)
                        if match:
                            bounce_info.bounce_code = match.group(1)
                            break

                    # Search for diagnostic codes
                    for pattern in diag_patterns:
                        match = re.search(pattern, email_body)
                        if match:
                            bounce_info.diagnostic_code = match.group(1)
                            break

                # Add to our list of bounced emails
                bounced_emails_info.append(bounce_info)

            return bounced_emails_info

        return []

    def check_replied_email(
        self,
        message_id: str,
        sender: str,
        host: str,
        port: int,
        email: str,
        password: str,
        since_date: timedelta = timedelta(weeks=2),
    ):
        try:
            service = self.auth(host, port, email, password)
            service.select("INBOX")

            # Format date according to IMAP RFC 3501 specification
            formatted_date = (datetime.now() - since_date).strftime("%d-%b-%Y")

            # First search for all emails in the given time period
            search_criteria = (
                f'HEADER "In-Reply-To" "{message_id}" SINCE "{formatted_date}"'
            )
            status, data = service.search(None, search_criteria)

            if not data[0]:
                return False

            # Get all message IDs in the date range
            msg_ids = data[0].split()

            # Instead of collecting details about all replies, just check if any reply exists
            for msg_id in msg_ids:
                # Fetch only the headers to check for In-Reply-To and References fields
                status, msg_data = service.fetch(msg_id, "(BODY.PEEK[HEADER])")
                if status != "OK":
                    continue
                # Parse headers
                email_headers = {}
                for part in msg_data:
                    if isinstance(part, tuple):
                        header_lines = part[1].split(b"\r\n")
                        for line in header_lines:
                            if line and b":" in line:
                                try:
                                    key, value = line.decode(
                                        "utf-8", errors="ignore"
                                    ).split(":", 1)
                                    email_headers[key.strip().lower()] = value.strip()
                                except Exception:
                                    continue

                # Check if this email is a reply to our target message
                in_reply_to = email_headers.get("in-reply-to", "")
                references = email_headers.get("references", "")
                from_address = email_headers.get("from", "")

                # Check if this message references our target message ID and is from the specified sender
                if message_id in in_reply_to or message_id in references:
                    # Additional check: verify the sender matches
                    # Remove suffix + in email. Example: test+1@gmail.com -> test@gmail.com
                    if trim_email(sender).lower() in trim_email(from_address).lower():
                        # Return basic information without fetching the full message body
                        return {
                            "subject": email_headers.get("subject", ""),
                            "from": from_address,
                            "date": email_headers.get("date", ""),
                        }
            # No matching reply found
            return False
        except Exception:
            return False
