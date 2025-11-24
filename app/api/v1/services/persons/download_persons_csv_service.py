# flake8: noqa: E501
import asyncio
import io
import zipfile
from datetime import datetime

import pandas as pd
from fastapi.responses import StreamingResponse
from fastapi_mail import FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from sqlmodel import Session, select

from app.api.base.deps import mail_connection
from app.api.base.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    PaymentRequiredException,
)
from app.api.v1.schemas.search_cross import DowloadCsvRequest, TypeDownload
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.base_service import remaining_credit
from app.api.v1.services.credits.consume_credit_service import consume_credit
from app.config import settings
from app.models import DownloadedHistory, TeamPerson
from app.models.export_history import ExportHistory, ExportStatus, ExportType
from app.models.person import Person
from app.models.team import PlanCode
from app.models.team_credit import ServiceCode
from external.s3 import S3Service
from utils.credit_utils import is_enough_credit


def download_persons_csv(
    db: Session,
    search_condition: DowloadCsvRequest,
    current_user: UserBase,
    listing_plan_code: PlanCode,
    is_background: bool = False,
):
    if (
        search_condition.list_person_uuids is not None
        and len(search_condition.list_person_uuids) > 10000
    ):
        raise ForbiddenException(detail="person.max_downloaded_item_read")

    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{current_user.team_id}/persons/人物のエクスポート_{timestamp}.zip"  # Define the S3 object name

    index = 0
    while True:
        exists = db.exec(
            select(ExportHistory).where(
                ExportHistory.team_id == current_user.team_id,
                ExportHistory.file_name == filename,
                ExportHistory.export_type == ExportType.PERSON,
            )
        ).first()
        if not exists:
            break
        index += 1
        filename = f"{current_user.team_id}/persons/人物のエクスポート_{timestamp} ({index}).zip"

    csv_filename = f"人物のエクスポート_{timestamp} ({index}).csv"
    export_history = ExportHistory(
        team_id=current_user.team_id,
        file_name=filename,
        export_type=ExportType.PERSON,
        amount=len(search_condition.list_person_uuids),
        status=ExportStatus.IN_PROGRESS,
    )
    db.add(export_history)
    db.flush()
    db.commit()
    status = ExportStatus.IN_PROGRESS
    try:
        if listing_plan_code is not PlanCode.UNLIMITED:
            list_person_export = get_list_person_download(
                db,
                current_user,
                search_condition.type_download,
                search_condition.list_person_uuids,
            )
        else:
            list_person_export = search_condition.list_person_uuids

        persons_query = (
            select(Person)
            .where(
                Person.uuid.in_(list_person_export),
                Person.deleted_at.is_(None),
            )
            .limit(10000)
            .order_by(Person.uuid)
        )
        persons = db.exec(persons_query).all()

        persons_dicts = [c.__dict__ for c in persons]

        temp_df = pd.DataFrame(persons_dicts)

        for index, row in temp_df.iterrows():
            if row["corporate_number"]:
                temp_df.at[index, "corporate_number"] = [
                    "--" if x is None else x for x in row["corporate_number"]
                ]

        temp_df = temp_df[
            [
                "name",
                "bio",
                "intro",
                "address",
                "role_name",
                "company_name",
                "corporate_number",
                "role_group_codes",
                "fb_url",
                "github_url",
                "linkedin_url",
                "twitter_url",
                "wantedly_url",
            ]
        ]

        temp_df.rename(
            columns={
                "address": "住所",
                "bio": "自己紹介",
                "fb_url": "フェイスブックのURL",
                "role_group_codes": "役職グループ",
                "role_name": "役職",
                "github_url": "ギットハブのURL",
                "corporate_number": "法人番号",
                "intro": "情報",
                "company_name": "企業名",
                "name": "氏名",
                "linkedin_url": "リンクインのURL",
                "twitter_url": "ツイッターのURL",
                "wantedly_url": "ワンテドリーのURL",
            },
            inplace=True,
        )

        # Convert dataframe to CSV in-memory
        csv_buffer = io.StringIO()
        temp_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as zip_file:
            zip_file.writestr(csv_filename, csv_buffer.getvalue())
        zip_buffer.seek(0)

        s3_service = S3Service()
        # Upload ZIP file to S3
        success = s3_service.put_object(
            object_name=filename,
            content=zip_buffer.getvalue(),
            content_type="application/zip",
        )

        if not success:
            raise BadRequestException(detail="common.uploadFileFailed")

        status = ExportStatus.AVAILABLE

        if not is_background:
            csv_buffer.seek(0)  # Reset the buffer position to the beginning
            filename = filename.split("/")[-1]  # Extract the file name from the S3 path
            return StreamingResponse(
                csv_buffer,
                status_code=200,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename.encode('utf-8').decode('latin-1')}"
                },
            )

        url = s3_service.generate_presigned_url(
            object_name=filename,
            expiration=60 * 60 * 24 * 30 * 6,  # 6 months
        )

        template_data = {
            "user_name": current_user.name,
            "url": url,
        }

        message = MessageSchema(
            subject="【SalesSmart】CSVエクスポートが完了しました",
            recipients=[EmailStr(current_user.email)],
            template_body=template_data,
            subtype=MessageType.html,
        )
        fm = FastMail(mail_connection())

        asyncio.run(fm.send_message(message, template_name="export_csv_mail.html"))
    except PaymentRequiredException as e:
        db.rollback()
        status = ExportStatus.CREDIT_ERROR
        raise e
    except Exception as e:
        db.rollback()
        status = ExportStatus.ERROR
        raise e
    finally:
        export_history.amount = len(list_person_export)
        export_history.status = status
        export_history.updated_at = datetime.now()
        db.add(export_history)
        db.commit()


def check_credit_download_person(
    db: Session,
    current_user: UserBase,
    type_download: TypeDownload,
    list_person_uuid_download,
):
    list_person_uuid_download = list(set(list_person_uuid_download))
    uuids_downloaded = (
        db.execute(
            select(TeamPerson.person_uuid)
            .where(
                TeamPerson.team_id == current_user.team_id,
                TeamPerson.person_uuid.in_(list_person_uuid_download),
            )
            .distinct(TeamPerson.person_uuid)
        )
        .scalars()
        .all()
    )
    if type_download == TypeDownload.CREDIT.value:
        lock_person = [
            item for item in list_person_uuid_download if item not in uuids_downloaded
        ]
    elif type_download == TypeDownload.DOWNLOADED.value:
        lock_person = []
        list_person_uuid_download = [
            item for item in list_person_uuid_download if item in uuids_downloaded
        ]
    amount_will_spend_download = settings.AMOUNT_PER_DOWNLOAD * len(lock_person)
    if not is_enough_credit(
        db,
        current_user.team_id,
        amount_will_spend_download,
        service_code=ServiceCode.PERSON,
    ):
        raise PaymentRequiredException(
            detail={
                "message": "person.notEnoughCredit",
                "remaining_credit": remaining_credit(
                    db, current_user.team_id, service_code=ServiceCode.PERSON
                ),
            }
        )
    amount_will_spend_export = settings.AMOUNT_PER_DOWNLOAD * len(
        list_person_uuid_download
    )
    if not is_enough_credit(
        db,
        current_user.team_id,
        amount_will_spend_export,
        service_code=ServiceCode.CSV,
    ):
        raise PaymentRequiredException(
            detail={
                "message": "person.notEnoughCreditExport",
                "remaining_credit": remaining_credit(
                    db, current_user.team_id, service_code=ServiceCode.CSV
                ),
            }
        )
    return lock_person, list_person_uuid_download


def get_list_person_download(
    db: Session,
    current_user: UserBase,
    type_download: TypeDownload,
    list_person_uuid_download,
):
    lock_person, list_person_uuid_download = check_credit_download_person(
        db, current_user, type_download, list_person_uuid_download
    )
    amount_will_spend_download = settings.AMOUNT_PER_DOWNLOAD * len(lock_person)
    amount_will_spend_export = settings.AMOUNT_PER_DOWNLOAD * len(
        list_person_uuid_download
    )
    if len(lock_person) > 10000:
        raise ConflictException(detail="common.hasTooManyPersons")
    try:
        team_companies = [
            TeamPerson(
                team_id=current_user.team_id,
                person_uuid=x,
            )
            for x in lock_person
        ]
        db.bulk_save_objects(team_companies)
        db.flush()

        downloaded_histories = DownloadedHistory(
            user_id=current_user.id,
            amount=amount_will_spend_download,
            service_code=ServiceCode.PERSON,
        )
        export_histories = DownloadedHistory(
            user_id=current_user.id,
            amount=amount_will_spend_export,
            service_code=ServiceCode.CSV,
        )
        db.add(downloaded_histories)
        db.add(export_histories)
        db.commit()
        consume_credit(
            db,
            current_user.team_id,
            amount_will_spend_download,
            service_code=ServiceCode.PERSON,
        )
        consume_credit(
            db,
            current_user.team_id,
            amount_will_spend_export,
            service_code=ServiceCode.CSV,
        )
    except Exception as e:
        db.rollback()
        raise e
    return list_person_uuid_download
