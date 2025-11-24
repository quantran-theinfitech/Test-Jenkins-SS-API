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
from app.constant.constants import INDUSTRIES_CATEGORIES, LISTING_MARKET_CODE
from app.models import DownloadedHistory, TeamCompany
from app.models.company import Company
from app.models.export_history import ExportHistory, ExportStatus, ExportType
from app.models.team import PlanCode
from app.models.team_company import StatusCode
from app.models.team_credit import ServiceCode
from external.s3 import S3Service
from utils.credit_utils import is_enough_credit


def download_companies_csv(
    search_condition: DowloadCsvRequest,
    current_user: UserBase,
    listing_plan_code: PlanCode,
    db: Session,
    is_background: bool = False,
):
    if (
        search_condition.list_company_corporate_numbers is not None
        and len(search_condition.list_company_corporate_numbers) > 10000
    ):
        raise ForbiddenException(detail="company.max_downloaded_item_read")

    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{current_user.team_id}/companies/企業のエクスポート_{timestamp}.zip"  # Define the S3 object name

    index = 0
    while True:
        exists = db.exec(
            select(ExportHistory).where(
                ExportHistory.team_id == current_user.team_id,
                ExportHistory.file_name == filename,
                ExportHistory.export_type == ExportType.CPN,
            )
        ).first()
        if not exists:
            break
        index += 1
        filename = (
            f"{current_user.team_id}/companies/企業のエクスポート_{timestamp} ({index}).zip"
        )

    csv_filename = f"企業のエクスポート_{timestamp} ({index}).csv"
    export_history = ExportHistory(
        team_id=current_user.team_id,
        file_name=filename,
        export_type=ExportType.CPN,
        amount=len(search_condition.list_company_corporate_numbers),
        status=ExportStatus.IN_PROGRESS,
    )
    db.add(export_history)
    db.flush()
    db.commit()
    status = ExportStatus.IN_PROGRESS
    try:
        list_company_export = []
        if listing_plan_code != PlanCode.UNLIMITED:
            list_company_export = get_list_company_download(
                db,
                current_user,
                search_condition.type_download,
                search_condition.list_company_corporate_numbers,
            )
        else:
            list_company_export = search_condition.list_company_corporate_numbers

        companies_query = (
            select(Company)
            .where(
                Company.corporate_number.in_(list_company_export),
                Company.deleted_at.is_(None),
            )
            .limit(10000)
            .order_by(Company.corporate_number)
        )
        companies = db.exec(companies_query).all()

        companies_dicts = [c.__dict__ for c in companies]

        temp_df = pd.DataFrame(companies_dicts)

        for index, row in temp_df.iterrows():
            industry_code = row.get("industry_code") if "industry_code" in row else None
            if industry_code:
                temp_df.at[index, "industry_code"] = INDUSTRIES_CATEGORIES.get(
                    industry_code, {}
                ).get("text", industry_code)
            sub_industries_code = row.get("sub_industries_code")
            sub_texts = []
            if sub_industries_code and isinstance(sub_industries_code, list):
                for code in sub_industries_code:
                    found = False
                    for industry in INDUSTRIES_CATEGORIES.values():
                        for child in industry.get("child", []):
                            if child["code"] == code:
                                sub_texts.append(child["text"])
                                found = True
                                break
                        if found:
                            break
            temp_df.at[index, "sub_industries_code"] = ";".join(
                text for text in sub_texts
            )
            listing_market_code = (
                row.get("listing_market_code") if "listing_market_code" in row else None
            )
            if listing_market_code:
                temp_df.at[index, "listing_market_code"] = LISTING_MARKET_CODE[
                    listing_market_code
                ]
        temp_df["revenue"].replace(0, None, inplace=True)
        temp_df["closing_month"].replace(0, None, inplace=True)
        temp_df["capital"].replace(0, None, inplace=True)
        temp_df["employees_count"].replace(0, None, inplace=True)
        temp_df = temp_df[
            [
                "corporate_number",
                "name",
                "hp_url",
                "industry_code",
                "sub_industries_code",
                "address",
                "closing_month",
                "business_content",
                "postal_code",
                "establish_at",
                "listing_market_code",
                "president_name",
                "phone",
                "fax",
                "contact_email",
                "recruit_phone",
                "recruit_email",
                "contact_form_url",
                "facebook_url",
                "twitter_url",
                "youtube_url",
                "employees_count",
                "capital",
                "revenue",
            ]
        ]
        temp_df.rename(
            columns={
                "corporate_number": "法人番号",
                "name": "企業名",
                "hp_url": "ウェブサイトURL(@を除く)",
                "industry_code": "大業界",
                "sub_industries_code": "中業界",
                "closing_month": "決算月",
                "address": "住所",
                "business_content": "事業内容",
                "postal_code": "郵便番号",
                "establish_at": "設立年月日",
                "listing_market_code": "上場区分",
                "president_name": "代表者名",
                "phone": "代表電話番号",
                "fax": "FAX番号",
                "contact_email": "代表メールアドレス",
                "recruit_phone": "採用電話番号",
                "recruit_email": "採用メールアドレス",
                "contact_form_url": "問い合わせフォーム",
                "facebook_url": "Facebook",
                "twitter_url": "Twitter",
                "youtube_url": "Youtube",
                "employees_count": "従業員数",
                "capital": "資本金 (万円)",
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
        export_history.amount = len(list_company_export)
        export_history.status = status
        export_history.updated_at = datetime.now()
        db.add(export_history)
        db.commit()


def check_credit_download_companies(
    db: Session,
    current_user: UserBase,
    type_download: TypeDownload,
    list_corporate_numbers_download,
):
    list_corporate_numbers_download = list(set(list_corporate_numbers_download))
    corporate_numbers_downloaded = (
        db.execute(
            select(TeamCompany.corporate_number)
            .where(
                TeamCompany.team_id == current_user.team_id,
                TeamCompany.corporate_number.in_(list_corporate_numbers_download),
            )
            .distinct(TeamCompany.corporate_number)
        )
        .scalars()
        .all()
    )
    if type_download == TypeDownload.CREDIT.value:
        lock_company = [
            item
            for item in list_corporate_numbers_download
            if item not in corporate_numbers_downloaded
        ]
    elif type_download == TypeDownload.DOWNLOADED.value:
        lock_company = []
        list_corporate_numbers_download = [
            item
            for item in list_corporate_numbers_download
            if item in corporate_numbers_downloaded
        ]
    amount_will_spend_download = settings.AMOUNT_PER_DOWNLOAD * len(lock_company)
    if not is_enough_credit(db, current_user.team_id, amount_will_spend_download):
        raise PaymentRequiredException(
            detail={
                "message": "company.notEnoughCredit",
                "remaining_credit": remaining_credit(db, current_user.team_id),
            }
        )
    amount_will_spend_export = settings.AMOUNT_PER_DOWNLOAD * len(
        list_corporate_numbers_download
    )
    if not is_enough_credit(
        db, current_user.team_id, amount_will_spend_export, ServiceCode.CSV
    ):
        raise PaymentRequiredException(
            detail={
                "message": "company.notEnoughCreditExport",
                "remaining_credit": remaining_credit(
                    db, current_user.team_id, ServiceCode.CSV
                ),
            }
        )

    return lock_company, list_corporate_numbers_download


def get_list_company_download(
    db: Session,
    current_user: UserBase,
    type_download: TypeDownload,
    list_corporate_numbers_download,
):
    lock_company, list_corporate_numbers_download = check_credit_download_companies(
        db,
        current_user,
        type_download,
        list_corporate_numbers_download,
    )
    amount_will_spend_download = settings.AMOUNT_PER_DOWNLOAD * len(lock_company)
    amount_will_spend_export = settings.AMOUNT_PER_DOWNLOAD * len(
        list_corporate_numbers_download
    )
    if len(lock_company) > 10000:
        raise ConflictException(detail="common.hasTooManyCompanies")
    try:
        team_companies = [
            TeamCompany(
                team_id=current_user.team_id,
                corporate_number=x,
                status_code=StatusCode.PENDING,
            )
            for x in lock_company
        ]
        db.bulk_save_objects(team_companies)
        db.flush()

        downloaded_histories = DownloadedHistory(
            user_id=current_user.id,
            amount=amount_will_spend_download,
            service_code=ServiceCode.CPN,
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
            service_code=ServiceCode.CPN,
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
    return list_corporate_numbers_download
