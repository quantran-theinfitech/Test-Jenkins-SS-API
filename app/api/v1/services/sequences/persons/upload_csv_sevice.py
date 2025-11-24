# flake8: noqa: E501

import io
import re
from typing import List, Optional

import chardet
import pandas as pd
from fastapi import UploadFile
from sqlmodel import Session, select, update

from app.api.base.exceptions import NotFoundException
from app.models.sequence.campaign import SequenceCampaign
from app.models.sequence.campaign_import import (
    SequenceCampaignImport,
    UploadProcessStatus,
)
from app.models.sequence.contact import SequenceContact
from app.models.sequence.step import SequenceCampaignStep, StepType
from app.models.team_credit import ServiceCode
from celery_worker import upload_sequence_contact
from celery_worker.upload_sequence_contact_service import save_to_db
from utils.credit_utils import is_enough_credit


def get_unique_name(
    name: str, existing_names: List[str], ext_name: Optional[bool] = True
) -> str:
    if name not in existing_names:
        return name
    if ext_name:
        base_name, ext = name.rsplit(".", 1)
    else:
        base_name = name
    match = re.match(r"(.*?)(?:\s\((\d+)\))?$", base_name)
    if match:
        base_name = match.group(1)
        current_number = int(match.group(2)) if match.group(2) else 0
    else:
        current_number = 0

    while True:
        current_number += 1
        new_name = (
            f"{base_name} ({current_number}).{ext}"
            if ext_name
            else f"{base_name} ({current_number})"
        )
        if new_name not in existing_names:
            return new_name


async def upload_csv_service(
    sequence_campaign_id: int,
    file: UploadFile,
    db: Session,
    team_id: int,
    skip_blank_contact: Optional[bool] = None,
):
    if not is_enough_credit(db, team_id, 1, ServiceCode.LINKEDIN_MSG):
        db.exec(
            update(SequenceCampaignStep)
            .where(
                SequenceCampaignStep.sequence_campaign_id == sequence_campaign_id,
                SequenceCampaignStep.step_type.in_(
                    [
                        StepType.LINKEDIN_AUTO_MESSAGE,
                        StepType.LINKEDIN_CONNECTION_REQUEST,
                        StepType.LINKEDIN_VIEW_PROFILE,
                    ]
                ),
                SequenceCampaignStep.deleted_at.is_(None),
            )
            .values(is_active=False)
        )

    elif not is_enough_credit(db, team_id, 1, ServiceCode.EMAIL):
        db.exec(
            update(SequenceCampaignStep)
            .where(
                SequenceCampaignStep.sequence_campaign_id == sequence_campaign_id,
                SequenceCampaignStep.step_type.in_(
                    [StepType.MAIL_MANUAL, StepType.MAIL_AUTO]
                ),
                SequenceCampaignStep.deleted_at.is_(None),
            )
            .values(is_active=False)
        )

    campaign = db.get(SequenceCampaign, sequence_campaign_id)
    if not campaign:
        raise NotFoundException("Campaign not found")
    response = {
        "success": False,
        "err_message": None,
        "request_skipping_blank_contact": False,
        "blank_contact_count": 0,
    }
    contents = await file.read()
    result = chardet.detect(contents)
    if result["encoding"].lower() != "utf-8":
        response["err_message"] = "sequence.invalidFileFormat"
        return response
    csv_text = contents.decode("utf-8")
    # Remove leading rows that are effectively empty (only commas/quotes/whitespace)
    lines = csv_text.splitlines()
    while lines and re.fullmatch(r"[\s,\"]*", lines[0]):
        lines.pop(0)
    csv_text = "\n".join(lines)
    csv_data = io.StringIO(csv_text)
    df = pd.read_csv(csv_data, on_bad_lines="skip", dtype=str)
    df = df.where(pd.notna(df), None)
    df = df.dropna(how="all")
    if "氏名" in df.columns:
        if "氏名(必須)" in df.columns:
            df.drop(columns=["氏名"], inplace=True)
    required_field = {
        "氏名(必須)": "氏名",
    }
    df.rename(columns=required_field, inplace=True)
    if "氏名" not in df.columns:
        response["err_message"] = "sequence.nameColumnIsRequired"
        return response
    if df["氏名"].isnull().any():
        response["err_message"] = "sequence.missingName"
        return response
    for col in ["メール", "リンクインのURL"]:
        if col not in df.columns:
            df[col] = None
    existed_emails = db.exec(
        select(SequenceContact.email).where(
            SequenceContact.sequence_campaign_id == sequence_campaign_id,
            SequenceContact.email.isnot(None),
            SequenceContact.deleted_at.is_(None),
        )
    ).all()
    if existed_emails:
        df.loc[df["メール"].isin(existed_emails), "メール"] = None
    existed_linkedin_urls = db.exec(
        select(SequenceContact.linkedin_url).where(
            SequenceContact.sequence_campaign_id == sequence_campaign_id,
            SequenceContact.linkedin_url.isnot(None),
            SequenceContact.deleted_at.is_(None),
        )
    ).all()
    if existed_linkedin_urls:
        df.loc[df["リンクインのURL"].isin(existed_linkedin_urls), "リンクインのURL"] = None

    df.loc[df.duplicated(subset=["メール"], keep="first"), "メール"] = None
    df.loc[df.duplicated(subset=["リンクインのURL"], keep="first"), "リンクインのURL"] = None
    if len(df) > 10000:
        response["err_message"] = "uploadfile.fileTooLarge"
        return response
    count = ((df["メール"].isnull()) | (df["リンクインのURL"].isnull())).sum()
    response["blank_contact_count"] = count
    existing_imports = db.exec(
        select(SequenceCampaignImport.name).where(
            SequenceCampaignImport.sequence_campaign_id == sequence_campaign_id,
            SequenceCampaignImport.team_id == team_id,
            SequenceCampaignImport.deleted_at.is_(None),
        )
    ).all()

    unique_name = get_unique_name(file.filename, existing_imports)

    campaign_import = SequenceCampaignImport(
        sequence_campaign_id=sequence_campaign_id,
        team_id=team_id,
        name=unique_name,
        upload_process_status=UploadProcessStatus.IN_PROGRESS.value,
    )
    db.add(campaign_import)
    db.flush()
    chunks = []
    chunk_size = 1000
    total = len(df)
    print(total)
    for start in range(0, total, chunk_size):
        chunks.append(df.iloc[start : start + chunk_size])
    result = save_to_db(
        campaign.dict(),
        chunks[0].to_dict(orient="records"),
        db,
        campaign_import.id,
        total,
        team_id,
    )

    if len(chunks) > 1:
        for idx, chunk in enumerate(chunks[1:]):
            db.refresh(campaign)
            is_last_chunk = idx == len(chunks) - 2
            chunk_data = chunk.to_dict(orient="records")
            upload_sequence_contact.apply_async(
                (
                    campaign.dict(),
                    chunk_data,
                    campaign_import.id,
                    is_last_chunk,
                    total,
                    team_id,
                ),
                time_limit=120,
            )
    if result:
        response["err_message"] = result
    else:
        response["success"] = True
    return response
