# flake8: noqa
from fastapi import HTTPException
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sqlmodel import Session, select

from app.api.base.exceptions import PaymentRequiredException
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mailboxes import refresh_mail_alias_service
from app.config import settings
from app.models.sequence.mailbox import MailboxType, SequenceMailbox
from app.models.team_credit import ServiceCode
from utils.credit_utils import consume_credit, is_enough_credit


def google_login_service():
    flow = InstalledAppFlow.from_client_config(
        {
            "web": {
                "project_id": settings.GOOGLE_PROJECT_ID,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        settings.GOOGLE_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    auth_url, _ = flow.authorization_url(prompt="consent")
    return auth_url


def google_callback_service(code: str, db: Session, current_user: UserBase):
    if not is_enough_credit(db, current_user.team_id, 1, ServiceCode.MAILBOX_CONNECT):
        raise PaymentRequiredException("sequence.notEnoughMailboxConnectQuota")
    flow = InstalledAppFlow.from_client_config(
        {
            "web": {
                "project_id": settings.GOOGLE_PROJECT_ID,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        settings.GOOGLE_SCOPES,
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    credentials = flow.credentials
    refresh_token = credentials.refresh_token

    # Sử dụng Google People API để lấy thông tin người dùng
    people_service = build("people", "v1", credentials=credentials)
    profile = (
        people_service.people()
        .get(resourceName="people/me", personFields="emailAddresses")
        .execute()
    )

    user_email = profile.get("emailAddresses", [])[0].get("value", "No email available")

    mailbox = db.exec(
        select(SequenceMailbox).where(
            SequenceMailbox.email == user_email,
            SequenceMailbox.team_id == current_user.team_id,
            SequenceMailbox.mailbox_type == MailboxType.GOOGLE_API,
            SequenceMailbox.deleted_at.is_(None),
        )
    ).first()
    if mailbox:
        raise HTTPException(status_code=400, detail="sequence.emailAlreadyExist")
    mailbox = SequenceMailbox(
        user_id=current_user.id,
        team_id=current_user.team_id,
        created_by=current_user.id,
        updated_by=current_user.id,
        email=user_email,
        google_refresh_token=refresh_token,
        mailbox_type=MailboxType.GOOGLE_API,
        emails_sent_per_day=50,
        emails_sent_per_hour=6,
        config_step_done=[1],
    )
    existed_mailbox = db.exec(
        select(SequenceMailbox).where(
            SequenceMailbox.team_id == current_user.team_id,
            SequenceMailbox.deleted_at.is_(None),
        )
    ).first()
    if existed_mailbox:
        mailbox.is_default = False
    else:
        mailbox.is_default = True
    db.add(mailbox)
    consume_credit(db, current_user.team_id, 1, ServiceCode.MAILBOX_CONNECT)
    db.commit()
    db.refresh(mailbox)
    refresh_mail_alias_service(mailbox.id, db)

    # gmail_service = build("gmail","v1", credentials=credentials)
    # pubsub_topic = f'projects/{settings.GOOGLE_PROJECT_ID}/topics/email-notification'
    # watch_request = {
    #     'labelIds': ['INBOX'],  # Theo dõi email trong hộp thư đến
    #     'topicName': pubsub_topic  # Chỉ định Pub/Sub Topic
    # }

    # try:
    #     response = gmail_service.users().watch(userId='me', body=watch_request).execute()
    #     print(f"Push Notification Watch Response: {response}")
    # except Exception as e:
    #     print(f"An error occurred: {e}")

    db.refresh(mailbox)
    return mailbox
