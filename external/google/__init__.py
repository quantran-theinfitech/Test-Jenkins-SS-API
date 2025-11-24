import base64
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import settings
from external.google.schema.gmail import (
    GoogleBounceInfo,
    InboxGmailDetail,
    ListingGmails,
)
from external.mautic import LoggingDecorator


class GoogleService(LoggingDecorator):
    @classmethod
    def exclude_logging(cls):
        return ["__init__", "gmail_auth_service"]

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET

    def gmail_auth_service(self, refresh_token: str):
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

        creds.refresh(Request())

        return build("gmail", "v1", credentials=creds)

    def send_email(
        self,
        email_to: str,
        subject: str,
        body: str,
        refresh_token: str,
        thread_id: Optional[str] = None,
        send_as: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ):
        service = self.gmail_auth_service(refresh_token)

        # Soạn email
        message = MIMEMultipart()
        if thread_id:
            prev_message = (
                service.users().messages().get(userId="me", id=thread_id).execute()
            )
            msg_id = ""
            for header in prev_message["payload"]["headers"]:
                if header["name"] == "Message-Id":
                    msg_id = header["value"]
            message["In-Reply-To"] = msg_id
            message["References"] = msg_id
            message["subject"] = "Re: " + subject
        else:
            message["subject"] = subject
        if send_as:
            message["from"] = send_as
        else:
            message["from"] = "me"
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)
        message["to"] = email_to
        msg = MIMEText(body, "html")
        message.attach(msg)

        raw_message = message.as_string()
        raw_message_bytes = base64.urlsafe_b64encode(
            raw_message.encode("utf-8")
        ).decode("utf-8")

        try:
            # Gửi email qua Gmail API
            message = (
                service.users()
                .messages()
                .send(
                    userId="me", body={"raw": raw_message_bytes, "threadId": thread_id}
                )
                .execute()
            )
            return {
                "success": True,
                "message_id": message["id"],
                "thread_id": message["threadId"],
            }
        except Exception as e:
            return {"success": False, "detail": e}

    def get_emails(self, refresh_token: str, max_results: int = 50):
        service = self.gmail_auth_service(refresh_token)

        # Lấy danh sách email từ Gmail
        results = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
            .execute()
        )
        messages = results.get("messages", [])

        # Lấy thông tin email chi tiết
        email_data = []
        for message in messages:
            msg = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )
            # Lọc thông tin từ các phần trong message
            for header in msg["payload"]["headers"]:
                if header["name"] == "Subject":
                    subject = header["value"]
                if header["name"] == "Sender":
                    sender = header["value"]
            # Lấy một đoạn nội dung email (snippet)
            body = msg["snippet"]
            email_details = InboxGmailDetail(sender=sender, subject=subject, body=body)
            email_data.append(email_details)

        return ListingGmails(gmails_list=email_data)

    def check_bounced_email(self, refresh_token: str, time_since_last_check: datetime):
        service = self.gmail_auth_service(refresh_token)
        try:
            time_stamp = int(time_since_last_check.timestamp())
            bounced_id_list = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    q=f"from: mailer-daemon@googlemail.com after: {time_stamp}",
                )
                .execute()
            )
        except Exception as e:
            raise e
        bounced_list = []
        messages = bounced_id_list.get("messages", [])
        for message in messages:
            bounced_mail = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )
            delivery_detail_status = bounced_mail["payload"]["parts"][1]["parts"][0]
            encoded_body = delivery_detail_status["body"]["data"]
            body = base64.urlsafe_b64decode(encoded_body).decode("utf-8")
            data = body.split("\r\n")
            for line in data:
                # if "Final-Recipient" in line:
                #     recipient = line.split(":")[1].strip()
                # if "Action" in line:
                #     action = line.split(":")[1].strip()
                if "Status" in line:
                    status = line.split(":")[1].strip()
                if "Diagnostic-Code" in line:
                    start = line.find("Diagnostic-Code") + len("Diagnostic-Code:")
                    diag_code = line[start:].strip()
            bounced_list.append(
                GoogleBounceInfo(
                    message_id=message["threadId"],
                    bounce_code=status,
                    diagnostic_code=diag_code,
                )
            )
        return bounced_list

    def check_replied_email(
        self,
        contact_email: str,
        thread_id: str,
        refresh_token: str,
    ):
        try:
            service = self.gmail_auth_service(refresh_token)
            messages = (
                service.users()
                .threads()
                .get(userId="me", id=thread_id, format="full")
                .execute()
            )
            for message in messages["messages"]:
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message["id"])
                    .execute()
                )
                headers = msg["payload"]["headers"]
                sender = next(
                    header["value"] for header in headers if header["name"] == "From"
                )
                if "<" in sender and ">" in sender:
                    sender = sender.split("<")[1].split(">")[0]
                base_local, domain = contact_email.lower().split("@", 1)
                base_local = base_local.split("+", 1)[0]
                pattern = (
                    r"^"
                    + re.escape(base_local)
                    + r"(?:\+[^@]+)?@"
                    + re.escape(domain)
                    + r"$"
                )
                if re.match(pattern, sender.lower()):
                    subject = next(
                        (
                            header["value"]
                            for header in headers
                            if header["name"] == "Subject"
                        ),
                        "No Subject",
                    )
                    body = ""
                    for part in msg["payload"]["parts"]:
                        if part["mimeType"] == "text/plain":
                            body = part["body"]["data"]
                            body = base64.urlsafe_b64decode(body).decode("utf-8")
                        elif part["mimeType"] == "text/html":
                            body = part["body"]["data"]
                            body = base64.urlsafe_b64decode(body).decode("utf-8")
                    print(f"Check replied mail from sender: {sender}")
                    print(f"Subject: {subject}")
                    print(f"Body: {body}")
                    return {"subject": subject, "body": body}
            return False
        except Exception as e:
            print(e)
            return False

    def get_mail_aliases(self, refresh_token: str):
        service = self.gmail_auth_service(refresh_token)
        aliases = service.users().settings().sendAs().list(userId="me").execute()
        return aliases.get("sendAs", [])
