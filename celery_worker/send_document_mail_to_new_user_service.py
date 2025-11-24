import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path
from typing import Any

import gspread
from fastapi_mail import ConnectionConfig, MessageSchema, MessageType
from google.oauth2.service_account import Credentials
from sqlmodel import Session

from app.config import settings

MAPPING = {
    "email": "メールアドレス",
    "first_name": "名",
    "last_name": "姓",
    "status": "メール送信済み",
    "failed_reason": "不合格理由",
}

GG_ACCOUNT = settings.SALESMART_GOOGLE_SERVICE_ACCOUNT
GG_SHEET_URL = settings.SALESMART_GOOGLE_SHEET_URL


async def send_document_mail_to_new_user_service(
    db: Session, mail_connection: ConnectionConfig
):
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    credentials = Credentials.from_service_account_info(
        json.loads(GG_ACCOUNT),
        scopes=SCOPES,
    )
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_url(GG_SHEET_URL)
    worksheet = spreadsheet.sheet1
    data = _get_all_records_as_strings(worksheet)

    # Determine the column index for the status flag once (1-indexed)
    headers = list(data[0].keys()) if data else []
    if MAPPING["status"] in headers:
        status_column_index = headers.index(MAPPING["status"]) + 1
    else:
        status_column_index = len(headers) + 1

    if MAPPING["failed_reason"] in headers:
        failed_reason_column_index = headers.index(MAPPING["failed_reason"]) + 1
    else:
        failed_reason_column_index = len(headers) + 2

    # Row number in the sheet starts from 2 because row 1 is the header
    for sheet_row_number, row in enumerate(data, start=2):
        email = row.get(MAPPING["email"])

        email_status = row.get(MAPPING["status"], "")

        # Skip if already processed
        if email_status:
            continue

        # (Email format validation removed as per request)

        if not email:
            print("Empty email cell, skipping...")
            worksheet.update_cell(sheet_row_number, status_column_index, "FALSE")
            worksheet.update_cell(
                sheet_row_number, failed_reason_column_index, "メールアドレスが空です"
            )
            _set_checkbox(worksheet, sheet_row_number, status_column_index)
            continue

        try:
            name = f"{row.get(MAPPING['last_name'])}{row.get(MAPPING['first_name'])}"
            content = {
                "user_name": name,
                "login_url": f"{settings.FE_URL}/login",
                "contact_url": f"{settings.LP_URL}/#contact-form",
            }
            message = MessageSchema(
                subject="【ご請求ありがとうございます】SalesSmartサービス概要資料のご送付",
                recipients=[email],
                template_body=content,
                subtype=MessageType.html,
            )
            send_mail(mail_connection, message, "document_mail_for_new_user.html")
            print(f"Email sent to {email}")
            worksheet.update_cell(sheet_row_number, status_column_index, "TRUE")
            _set_checkbox(worksheet, sheet_row_number, status_column_index)
        except Exception as e:
            print(f"Error sending email to {email}: {e}")
            worksheet.update_cell(sheet_row_number, status_column_index, "FALSE")
            worksheet.update_cell(
                sheet_row_number,
                failed_reason_column_index,
                f"メール送信に失敗しました. {e}",
            )
            _set_checkbox(worksheet, sheet_row_number, status_column_index)
    print("Finished processing rows in the Google Sheet")


def _get_all_records_as_strings(sheet, empty2zero=False, head=1):
    """Recreate `get_all_records()` but force everything to stay as strings."""
    data = sheet.get_all_values()
    headers = data[head - 1]
    records = []

    for row in data[head:]:
        # Extend the row if it's shorter than headers
        row += [""] * (len(headers) - len(row))

        record = {}
        for key, value in zip(headers, row):
            if value == "" and empty2zero:
                value = "0"
            record[key] = value
        records.append(record)

    return records


def _set_checkbox(worksheet: gspread.Worksheet, row_idx: int, col_idx: int) -> None:
    """Convert a single cell to a checkbox type via DataValidation."""
    sheet_id = worksheet._properties.get("sheetId")  # type: ignore[index]
    if sheet_id is None:
        return
    request_body: dict[str, Any] = {
        "requests": [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row_idx - 1,
                        "endRowIndex": row_idx,
                        "startColumnIndex": col_idx - 1,
                        "endColumnIndex": col_idx,
                    },
                    "rule": {
                        "condition": {"type": "BOOLEAN"},
                        "strict": True,
                        "showCustomUi": True,
                    },
                }
            }
        ]
    }
    worksheet.spreadsheet.batch_update(request_body)


def send_mail(connection: ConnectionConfig, message: MessageSchema, template_name: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = message.subject
        msg["From"] = formataddr((connection.MAIL_FROM_NAME, connection.MAIL_FROM))
        msg["To"] = ", ".join(message.recipients)

        html_content = _render_template(template_name, message.template_body)
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        with smtplib.SMTP(connection.MAIL_SERVER, connection.MAIL_PORT) as server:
            if connection.MAIL_STARTTLS:
                server.starttls()

            if connection.USE_CREDENTIALS:
                server.login(connection.MAIL_USERNAME, connection.MAIL_PASSWORD)

            server.send_message(msg)

        print(
            f"Email sent successfully to {message.recipients} using template {template_name}"
        )
        return True
    except Exception as e:
        print(f"Unexpected error sending email: {e}")
        return False


def _render_template(template_name: str, template_body: dict) -> str:
    try:
        template_folder = Path(__file__).parent.parent / "app/api/v1/templates"
        template_path = template_folder / template_name

        if not template_path.exists():
            print(f"Template file not found: {template_path}")
            return f"<p>Template '{template_name}' not found.</p>"

        with open(template_path, encoding="utf-8") as f:
            template_content = f.read()

        rendered_content = template_content
        for key, value in template_body.items():
            placeholder = f"{{{{{key}}}}}"
            rendered_content = rendered_content.replace(placeholder, str(value))

        return rendered_content

    except Exception as e:
        print(f"Error rendering template {template_name}: {e}")
        return f"<p>Error rendering template: {e}</p>"
