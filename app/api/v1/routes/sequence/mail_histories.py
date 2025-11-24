# flake8: noqa: E501
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import distinct, select
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.sequence.mail_histories import (
    ChangeMailboxMailHistoryRequest,
    DeleteMailHistoryRequest,
    ListingMailHistoryRequest,
    ListingMailHistoryResponse,
    MailHistoryStatistics,
    RescheduleMailHistoryStatusRequest,
    RetryMailHistoryRequest,
    SkipMailHistoryStatusRequest,
)
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.mail_histories import (
    change_mailbox_service,
    delete_mail_history_service,
    get_mail_history_statistics_with_view_service,
    listing_mail_histories_with_view_service,
    retry_mail_history_service,
    skip_mail_history_service,
    trigger_open_email_service,
    unscribe_email_service,
)
from app.api.v1.services.sequences.mail_histories.update_mail_history_service import (
    reschedule_mail_history_service,
)
from app.api.v1.services.sequences.mail_histories.verify_campaign_permisstion_service import (
    verify_campaign_permission,
)
from app.models.sequence.campaign_import import SequenceCampaignImport
from app.models.sequence.campaign_import_item import SequenceCampaignImportItem
from app.models.sequence.mail_history import MailHistoryStatus
from app.models.user import User

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get(
    "/{sequence_campaign_id}/mail_histories", response_model=ListingMailHistoryResponse
)
def listing_mail_histories(
    sequence_campaign_id: int,
    sequence_campaign_import_ids: Optional[str] = Query(None),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    status: Optional[MailHistoryStatus] = Query(None),
    mailbox_ids: Optional[str] = Query(None),
    mail_senders: Optional[List[str]] = Query(None),
    contact_ids: Optional[str] = Query(None),
    step_ids: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    verify_campaign_permission(db, current_user, sequence_campaign_id)
    request = ListingMailHistoryRequest(
        page=page,
        per_page=per_page,
        status=status,
        keyword=keyword,
        mail_senders=mail_senders,
    )
    mails = []
    alias_emails = []
    if mailbox_ids:
        for mailbox_id in mailbox_ids.split(","):
            mail = mailbox_id.split("_")
            if len(mail) > 1:
                alias_emails.extend([int(m) for m in mail[1:]])
            else:
                mails.append(int(mail[0]))
    if step_ids:
        request.step_ids = [int(step_id) for step_id in step_ids.split(",")]
    if contact_ids:
        request.contact_ids = [int(contact_id) for contact_id in contact_ids.split(",")]
    if sequence_campaign_import_ids:
        sequence_campaign_import_ids = [
            int(id) for id in sequence_campaign_import_ids.split(",")
        ]
        import_records = db.exec(
            select(SequenceCampaignImport).where(
                SequenceCampaignImport.id.in_(
                    [int(id) for id in sequence_campaign_import_ids]
                ),
                SequenceCampaignImport.sequence_campaign_id == sequence_campaign_id,
                SequenceCampaignImport.deleted_at.is_(None),
            )
        ).all()
        if import_records:
            import_items = db.exec(
                select(distinct(SequenceCampaignImportItem.sequence_contact_id)).where(
                    SequenceCampaignImportItem.sequence_campaign_import_id.in_(
                        sequence_campaign_import_ids
                    ),
                    SequenceCampaignImportItem.deleted_at.is_(None),
                )
            ).all()
            request.contact_ids = list(
                {item[0] for item in import_items if item[0] is not None}
            )

    mail_histories, total = listing_mail_histories_with_view_service(
        db, sequence_campaign_id, request, current_user
    )
    return ListingMailHistoryResponse(
        page=page,
        per_page=per_page,
        total=total,
        data=mail_histories,
    )


@router.get(
    "/{sequence_campaign_id}/mail_histories/statistics",
    response_model=MailHistoryStatistics,
)
def get_mail_histories_statistics(
    sequence_campaign_id: int,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    return get_mail_history_statistics_with_view_service(
        db, sequence_campaign_id, current_user
    )


@router.put("/mail_histories/reschedule")
def reschedule_mail_history(
    request: RescheduleMailHistoryStatusRequest,
    db: Session = Depends(get_session),
):
    if not reschedule_mail_history_service(db, request):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allMailsFinished")


@router.put("/mail_histories/skip")
def skip_mail_history(
    request: SkipMailHistoryStatusRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    if not skip_mail_history_service(db, request, current_user):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allMailsFinished")


@router.put("/mail_histories/retry")
def retry_mail_history(
    request: RetryMailHistoryRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    if not retry_mail_history_service(db, request, current_user):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allMailsFinished")


@router.put("/mail_histories/change_mailbox")
def change_mailbox_mail_history(
    request: ChangeMailboxMailHistoryRequest,
    db: Session = Depends(get_session),
    current_user: UserBase = Depends(get_current_user()),
):
    if not change_mailbox_service(db, request, current_user):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allMailsFinished")


@router.put("/mail_histories/delete")
def delete_mail_history(
    request: DeleteMailHistoryRequest,
    db: Session = Depends(get_session),
):
    success = delete_mail_history_service(db, request)
    return {"success": success}


@router.get("/mail_histories/open")
def trigger_mail_opened(
    background_tasks: BackgroundTasks,
    tracking_token: Optional[str] = Query(None),
    db: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_user(raise_exception=False)),
):
    print(f"Email with token {tracking_token} opened")
    background_tasks.add_task(
        trigger_open_email_service, db, tracking_token, current_user
    )


@router.get("/unscribe")
def sequence_unsubcribe(
    tracking_token: Optional[str] = Query(None),
    db: Session = Depends(get_session),
):
    success = unscribe_email_service(db, tracking_token)
    return {"success": success}
