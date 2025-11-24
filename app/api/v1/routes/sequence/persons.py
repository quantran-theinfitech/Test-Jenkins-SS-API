from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.base.deps import custom_generate_unique_id, get_session
from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.sequence.persons import (
    CampaignImportList,
    ChangeSequencePersonMailbox,
    ListingSequencePersonsResponse,
    SequenceContactUploadResponse,
    SequencePersonDetail,
    SequencePersonStageResponse,
    SequencePersonStageStatistic,
    SortField,
    SortOrder,
    StatusEnum,
    UpdateSequencePersonRequest,
    UpdateSequencePersonStageRequest,
)
from app.api.v1.services.sequences.persons import (
    change_sequence_person_mailbox_service,
    delete_sequence_persons_service,
    get_detail_sequence_person_service,
    get_sequence_campaign_imports_service,
    get_sequence_person_stage_count,
    listing_sequence_persons_service,
    update_sequence_person_service,
    update_sequence_person_stage_service,
    upload_csv_service,
)

router = APIRouter(generate_unique_id_function=custom_generate_unique_id)


@router.get(
    "/{sequence_campaign_id}/persons", response_model=ListingSequencePersonsResponse
)
def listing_sequence_persons(
    sequence_campaign_id: int,
    current_step: Optional[List[int]] = Query([]),
    mail_senders: Optional[List[str]] = Query(None),
    order: Optional[SortOrder] = Query(default=SortOrder.DESC),
    field: Optional[SortField] = Query(default=SortField.CREATED_AT),
    keyword: Optional[str] = Query(None),
    status: Optional[List[StatusEnum]] = Query([]),
    linkedin_senders: Optional[List[str]] = Query(default=None),
    per_page: Optional[int] = Query(default=5, ge=1),
    page: Optional[int] = Query(default=1, ge=1),
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user()),
):
    # mails = []
    # alias_emails = []
    # if emails:
    #     for email in emails:
    #         mail = email.split("_")
    #         mails.append(mail[0])
    #         alias_emails.extend(mail[1:])
    listing, total, process_status = listing_sequence_persons_service(
        db,
        sequence_campaign_id,
        page,
        per_page,
        current_user,
        mail_senders,
        current_step,
        order,
        field,
        keyword,
        status,
        linkedin_senders,
    )
    return ListingSequencePersonsResponse(
        page=page,
        per_page=per_page,
        total=total,
        data=listing,
        import_process_status=process_status,
    )


@router.get(
    "/{sequence_campaign_id}/persons/statistics",
    response_model=SequencePersonStageStatistic,
)
def get_sequence_persons_statistics(
    sequence_campaign_id: int,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user()),
):
    return get_sequence_person_stage_count(db, sequence_campaign_id, current_user)


@router.post(
    "/{sequence_campaign_id}/persons/csv",
    status_code=201,
    response_model=SequenceContactUploadResponse,
)
async def create_csv(
    sequence_campaign_id: int,
    file: UploadFile,
    skip_blank_contact: Optional[bool] = None,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user()),
):
    if file.filename.endswith(".csv"):
        resp = await upload_csv_service(
            sequence_campaign_id, file, db, current_user.team_id, skip_blank_contact
        )
        if resp.get("err_message", None):
            raise HTTPException(status_code=400, detail=resp["err_message"])
        else:
            return resp
    else:
        raise HTTPException(status_code=400, detail="sequence.invalidFileFormat")


@router.get(
    "/{sequence_campaign_id}/persons/imports", response_model=CampaignImportList
)
def get_sequence_campaign_imports(
    sequence_campaign_id: int,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user()),
):
    return get_sequence_campaign_imports_service(sequence_campaign_id, db, current_user)


@router.delete("/", response_model=List[int])
def delete_sequence_persons(
    sequence_persons_ids: List[int],
    db: Session = Depends(get_session),
):
    return delete_sequence_persons_service(db, sequence_persons_ids)


@router.get("/{sequence_campaign_id}/persons/{current_step}")
def search_person_by_step(
    sequence_campaign_id: int,
    current_step: int,
):
    return 1


@router.get(
    "/{sequence_campaign_id}/person/{person_id}", response_model=SequencePersonDetail
)
def get_detail_sequence_person(
    sequence_campaign_id: int,
    person_id: int,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user()),
):
    return get_detail_sequence_person_service(sequence_campaign_id, person_id, db)


@router.put("/{sequence_campaign_id}/person/{person_id}")
def update_sequence_person(
    sequence_campaign_id: int,
    person_id: int,
    request: UpdateSequencePersonRequest,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user()),
):
    return update_sequence_person_service(
        sequence_campaign_id, person_id, request, db, current_user
    )


@router.put(
    "/campaigns/{campaign_id}/stage", response_model=SequencePersonStageResponse
)
def update_sequence_person_stage(
    campaign_id: int,
    request: UpdateSequencePersonStageRequest,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user()),
):
    update_sequence_person_stage_service(campaign_id, request, db, current_user)
    return JSONResponse(status_code=200, content={"success": True})


@router.put("/campaigns/{campaign_id}/change_mailbox")
def change_sequence_person_mailbox(
    campaign_id: int,
    request: ChangeSequencePersonMailbox,
    db: Session = Depends(get_session),
):
    if not change_sequence_person_mailbox_service(campaign_id, request, db):
        return JSONResponse(status_code=200, content={"success": True})
    else:
        raise HTTPException(status_code=400, detail="sequence.allContactsFinished")
