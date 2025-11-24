# flake8: noqa: E501
import io
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# from sqlalchemy import select, join
import chardet
import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import aliased
from sqlmodel import Session, and_, case, func, select, update

from app.api.base.exceptions import NotFoundException
from app.api.v1.schemas.enrichments import (
    EnrichmentCreate,
    EnrichmentFileDelimiter,
    EnrichmentFileEncoding,
    EnrichmentResponse,
    EnrichmentUpdate,
    EnrichmentVerifyFileResponse,
)
from app.api.v1.schemas.search_cross import CorporateNumberByIdentified
from app.api.v1.schemas.users import UserBase
from app.api.v1.services.sequences.persons.upload_csv_sevice import get_unique_name
from app.models.company import Company
from app.models.enrichment import (
    Enrichment,
    EnrichmentStatus,
    EnrichmentType,
    EnrichmentUploadFileMethod,
)
from app.models.enrichment_file import EnrichmentFile
from app.models.enrichment_item import EnrichmentItem
from app.models.enrichment_item_data import EnrichmentItemData
from app.models.sequence.campaign_import import UploadProcessStatus
from app.models.team import PlanCode
from app.models.team_company import TeamCompany
from celery_worker import upload_enrichment_item_from_file
from utils.enrichment.s3 import save_file_to_s3
from utils.enrichment.utils import file_compatible_check
from utils.extract_domain import extract_full_domain_url

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


def create_enrichment(
    db: Session, enrichment: EnrichmentCreate, team_id: int, user_id: int
) -> Enrichment:
    db_enrichment = Enrichment(
        name=enrichment.name,
        type=enrichment.type,
        team_id=team_id,
        column_json_mapping={},
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(db_enrichment)
    db.commit()
    db.refresh(db_enrichment)
    return db_enrichment


def get_enrichment(
    db: Session,
    enrichment_id: int,
    team_id: int,
    listing_plan_code: PlanCode,
    page: int = 1,
    per_page: int = 10,
) -> EnrichmentResponse:
    enrichment = db.exec(
        select(Enrichment).where(
            Enrichment.id == enrichment_id,
            Enrichment.team_id == team_id,
            Enrichment.deleted_at.is_(None),
        )
    ).first()

    if not enrichment:
        raise NotFoundException(detail="enrichments.enrichmentNotFound")

    start_idx = (page - 1) * per_page
    enrichment_files = db.exec(
        select(EnrichmentFile).where(
            EnrichmentFile.enrichment_id == enrichment_id,
            EnrichmentFile.upload_process_status
            == UploadProcessStatus.IN_PROGRESS.value,
        )
    ).all()
    upload_process_status = UploadProcessStatus.FINISHED.value
    for enrichment_file in enrichment_files:
        if enrichment_file.created_at < datetime.now() - timedelta(hours=3):
            enrichment_file.upload_process_status = UploadProcessStatus.FAILED.value
            continue
        upload_process_status = UploadProcessStatus.IN_PROGRESS.value
    enrichment_items = db.exec(
        select(EnrichmentItem)
        .where(
            EnrichmentItem.enrichment_id == enrichment_id,
            EnrichmentItem.deleted_at.is_(None),
        )
        .order_by(EnrichmentItem.entity_identifier.is_(None), EnrichmentItem.id)
        .offset(start_idx)
        .limit(per_page)
    ).all()

    total_items = db.exec(
        select(func.count(EnrichmentItem.id)).where(
            EnrichmentItem.enrichment_id == enrichment_id,
            EnrichmentItem.deleted_at.is_(None),
        )
    ).first()

    total_identified = db.exec(
        select(func.count(EnrichmentItem.id)).where(
            EnrichmentItem.enrichment_id == enrichment_id,
            EnrichmentItem.deleted_at.is_(None),
            EnrichmentItem.entity_identifier.is_not(None),
        )
    ).first()

    item_ids = [item.id for item in enrichment_items]
    item_data = db.exec(
        select(EnrichmentItemData).where(
            EnrichmentItemData.enrichment_item_id.in_(item_ids),
            EnrichmentItemData.deleted_at.is_(None),
        )
    ).all()

    item_data_map = {}
    for data in item_data:
        if data.enrichment_item_id not in item_data_map:
            item_data_map[data.enrichment_item_id] = []
        item_data_map[data.enrichment_item_id].append(data)

    columns = []
    total_columns_mapped = 0
    total_columns_uploaded = len(enrichment.column_json_mapping)

    column_map = {}
    for mapping_id, mapping in enrichment.column_json_mapping.items():
        columns.append(
            {
                "upload_column": mapping["upload_column"],
                "service_column": mapping["service_column"],
            }
        )
        column_map[mapping_id] = mapping["upload_column"]
        if mapping["service_column"]:
            total_columns_mapped += 1

    entity_identifiers = [
        item.entity_identifier
        for item in enrichment_items
        if item.entity_identifier is not None
    ]

    companies = {}
    if entity_identifiers:
        companies_query = (
            select(
                Company.corporate_number,
                Company.name,
                Company.hp_url,
                TeamCompany.corporate_number.label("is_downloaded"),
            )
            .outerjoin(
                TeamCompany,
                (TeamCompany.corporate_number == Company.corporate_number)
                & (TeamCompany.team_id == team_id),
            )
            .where(Company.corporate_number.in_(entity_identifiers))
        )

        companies_data = db.exec(companies_query).all()

        for company in companies_data:
            companies[company.corporate_number] = {
                "name": company.name,
                "hp_url": company.hp_url,
                "is_downloaded": (
                    company.is_downloaded is not None
                    if listing_plan_code != PlanCode.UNLIMITED
                    else True
                ),
            }

    # collections_map = {}
    # if companies:
    #     collections_data = db.exec(
    #         select(
    #             CompanyCollectionItem.corporate_number,
    #             CompanyCollection.id,
    #             CompanyCollection.name,
    #         )
    #         .join(
    #             CompanyCollection,
    #             CompanyCollectionItem.collection_id == CompanyCollection.id,
    #         )
    #         .where(
    #             CompanyCollectionItem.corporate_number.in_(companies.keys()),
    #             CompanyCollectionItem.deleted_at.is_(None),
    #             CompanyCollection.deleted_at.is_(None),
    #             CompanyCollection.team_id == team_id,
    #         )
    #     ).all()

    #     for corporate_number, collection_id, collection_name in collections_data:
    #         if corporate_number not in collections_map:
    #             collections_map[corporate_number] = []

    #         if not any(
    #             c["collection_id"] == collection_id
    #             for c in collections_map[corporate_number]
    #         ):
    #             collections_map[corporate_number].append(
    #                 {"collection_id": collection_id, "collection_name": collection_name}
    #             )

    if listing_plan_code == PlanCode.UNLIMITED:
        corporate_numbers_downloaded = entity_identifiers
    else:
        corporate_numbers_downloaded = db.exec(
            select(TeamCompany.corporate_number)
            .where(TeamCompany.team_id == team_id)
            .where(TeamCompany.corporate_number.in_(entity_identifiers))
        ).all()

    rows = []
    for item in enrichment_items:
        row = {col["upload_column"]: "" for col in columns}
        row["id"] = item.id
        for item_data in item_data_map.get(item.id, []):
            if str(item_data.column_json_mapping_id) in column_map:
                column_name = column_map[str(item_data.column_json_mapping_id)]
                row[column_name] = item_data.value

        row["entity_identifier"] = {
            "status": item.status,
            "entity_identifier": item.entity_identifier,
        }
        # row["collections"] = None

        if (
            item.entity_identifier
            and item.entity_identifier in companies
            and enrichment.status != EnrichmentStatus.FAILED
        ):
            company = companies[item.entity_identifier]
            domain_url = extract_full_domain_url(company.get("hp_url"))
            if domain_url:
                favicon_url = f"{domain_url}/favicon.ico"
            else:
                favicon_url = None
            row["entity_identifier"] = {
                "corporate_number": item.entity_identifier,
                "is_downloaded": company["is_downloaded"],
                "company_name": company["name"],
                "hp_url": company["hp_url"],
                "favicon_url": favicon_url,
                "status": item.status,
            }
            # row["collections"] = collections_map.get(item.entity_identifier, [])
        else:
            hp_url = row.get("hp_url")
            domain_url = extract_full_domain_url(hp_url)
            if domain_url:
                row["favicon_url"] = f"{domain_url}/favicon.ico"
            else:
                row["favicon_url"] = None

        rows.append(row)

    table_enrichment_response = {
        "columns": columns,
        "rows": rows,
        "page": page,
        "per_page": per_page,
        "total": total_items,
        "identified_rows": total_identified,
        "total_columns_uploaded": total_columns_uploaded,
        "total_columns_mapped": total_columns_mapped,
    }

    return EnrichmentResponse(
        id=enrichment.id,
        team_id=enrichment.team_id,
        name=enrichment.name,
        type=enrichment.type,
        status=enrichment.status,
        process_status=upload_process_status,
        created_at=enrichment.created_at,
        created_by=enrichment.created_by,
        updated_at=enrichment.updated_at,
        updated_by=enrichment.updated_by,
        deleted_at=enrichment.deleted_at,
        deleted_by=enrichment.deleted_by,
        table_enrichment_response=table_enrichment_response,
    )


def update_enrichment(
    db: Session,
    enrichment_id: int,
    enrichment_update: EnrichmentUpdate,
    team_id: int,
    user_id: int,
    listing_plan_code: PlanCode,
) -> EnrichmentResponse:
    query = select(Enrichment).where(
        Enrichment.id == enrichment_id,
        Enrichment.team_id == team_id,
        Enrichment.deleted_at.is_(None),
    )
    db_enrichment = db.exec(query).first()
    if not db_enrichment:
        raise NotFoundException(detail="enrichments.enrichmentNotFound")

    name = enrichment_update.name
    if name:
        db_enrichment.name = name

        db_enrichment.updated_by = user_id
        db.add(db_enrichment)
        db.commit()
        db.refresh(db_enrichment)

        return get_enrichment(db, enrichment_id, team_id, listing_plan_code)
    else:
        raise HTTPException(
            status_code=400, detail="enrichments.enrichmentNameRequired"
        )


def update_column_json_mapping(
    db: Session,
    enrichment_id: int,
    column_json_mapping: dict,
    team_id: int,
    user_id: int,
):
    query = select(Enrichment).where(
        Enrichment.id == enrichment_id,
        Enrichment.team_id == team_id,
        Enrichment.deleted_at.is_(None),
    )
    db_enrichment = db.exec(query).first()

    if not db_enrichment:
        raise NotFoundException(detail="enrichments.enrichmentNotFound")

    if column_json_mapping:
        incoming_mapping = {}
        for item in column_json_mapping:
            if (
                isinstance(item, dict)
                and "upload_column" in item
                and "service_column" in item
            ):
                incoming_mapping[item["upload_column"]] = item["service_column"]

        existing_mapping = db_enrichment.column_json_mapping or {}

        updated_mapping = {}
        for key, value in existing_mapping.items():
            if value.get("upload_column") in incoming_mapping:
                updated_mapping[key] = {
                    "upload_column": value["upload_column"],
                    "service_column": incoming_mapping[value["upload_column"]],
                }
            else:
                updated_mapping[key] = value

        db_enrichment.column_json_mapping = updated_mapping

        db_enrichment.updated_by = user_id
        db.add(db_enrichment)
        db.commit()
        db.refresh(db_enrichment)
    else:
        raise HTTPException(
            status_code=400, detail="enrichments.enrichmentColumnJsonMappingRequired"
        )


def delete_enrichment(
    db: Session,
    enrichment_id: int,
    team_id: int,
    user_id: int,
    listing_plan_code: PlanCode,
) -> Optional[EnrichmentResponse]:
    query = select(Enrichment).where(
        Enrichment.id == enrichment_id,
        Enrichment.team_id == team_id,
        Enrichment.deleted_at.is_(None),
    )
    db_enrichment = db.exec(query).first()
    if not db_enrichment:
        raise NotFoundException(detail="enrichments.enrichmentNotFound")

    delete_response = get_enrichment(db, enrichment_id, team_id, listing_plan_code)

    enrichment_files = db.exec(
        select(EnrichmentFile).where(
            EnrichmentFile.enrichment_id == enrichment_id,
            EnrichmentFile.deleted_at.is_(None),
        )
    ).all()

    for enrichment_file in enrichment_files:
        enrichment_file.deleted_by = user_id
        enrichment_file.deleted_at = datetime.now()
        db.add(enrichment_file)

    enrichment_items = db.exec(
        select(EnrichmentItem).where(
            EnrichmentItem.enrichment_id == enrichment_id,
            EnrichmentItem.deleted_at.is_(None),
        )
    ).all()

    for enrichment_item in enrichment_items:
        enrichment_item.deleted_by = user_id
        enrichment_item.deleted_at = datetime.now()
        db.add(enrichment_item)

    db_enrichment.deleted_by = user_id
    db_enrichment.deleted_at = datetime.now()
    db.add(db_enrichment)
    db.commit()
    db.refresh(db_enrichment)

    return delete_response


def duplicate_enrichment(
    db: Session,
    enrichment_id: int,
    team_id: int,
    user_id: int,
    listing_plan_code: PlanCode,
) -> EnrichmentResponse:
    query = select(Enrichment).where(
        Enrichment.id == enrichment_id,
        Enrichment.team_id == team_id,
        Enrichment.deleted_at.is_(None),
    )
    original_enrichment = db.exec(query).first()
    if not original_enrichment:
        raise NotFoundException(detail="enrichments.enrichmentNotFound")

    base_name, extension = os.path.splitext(original_enrichment.name)
    copy = "copy"
    base_name = re.sub(r"( copy(?: \d+)?)$", "", base_name)
    base_name_copy = f"{base_name} {copy} "
    query = select(Enrichment).where(
        Enrichment.team_id == team_id,
        Enrichment.deleted_at.is_(None),
    )
    all_enrichments = db.exec(query).all()
    max_num = 0
    for enrichment in all_enrichments:
        if enrichment.name.startswith(base_name_copy):
            suffix = enrichment.name[len(base_name_copy) :]  # noqa: E203

            match = re.match(r"(\d+)", suffix)
            if match:
                number_found = int(match.group(1))
                if number_found > max_num:
                    max_num = number_found
        elif enrichment.name == f"{base_name} {copy}{extension}":
            max_num = 1

    if max_num == 0:
        new_name = f"{base_name} {copy}{extension}"
    else:
        new_name = f"{base_name} {copy} {max_num + 1}{extension}"

    new_enrichment = Enrichment(
        name=new_name,
        type=original_enrichment.type,
        team_id=team_id,
        column_json_mapping=original_enrichment.column_json_mapping,
        created_by=user_id,
        updated_by=user_id,
        status=original_enrichment.status,
    )
    db.add(new_enrichment)
    db.commit()
    db.refresh(new_enrichment)

    enrichment_files = db.exec(
        select(EnrichmentFile).where(
            EnrichmentFile.enrichment_id == enrichment_id,
            EnrichmentFile.deleted_at.is_(None),
        )
    ).all()

    add_enrichment_file = []
    for enrichment_file in enrichment_files:
        new_enrichment_file = EnrichmentFile(
            enrichment_id=new_enrichment.id,
            file_name=enrichment_file.file_name,
            encoding=enrichment_file.encoding,
            delimiter=enrichment_file.delimiter,
            created_by=user_id,
            updated_by=user_id,
        )
        add_enrichment_file.append(new_enrichment_file)
    db.add_all(add_enrichment_file)

    enrichment_items = db.exec(
        select(EnrichmentItem).where(
            EnrichmentItem.enrichment_id == enrichment_id,
            EnrichmentItem.deleted_at.is_(None),
        )
    ).all()

    add_enrichment_item = []
    for enrichment_item in enrichment_items:
        new_enrichment_item = EnrichmentItem(
            enrichment_id=new_enrichment.id,
            enrichment_file_id=enrichment_item.enrichment_file_id,
            entity_identifier=enrichment_item.entity_identifier,
            created_by=user_id,
            updated_by=user_id,
        )
        add_enrichment_item.append(new_enrichment_item)
    db.add_all(add_enrichment_item)
    db.commit()

    item_data_map = {}
    for item in enrichment_items:
        item_data = db.exec(
            select(EnrichmentItemData).where(
                EnrichmentItemData.enrichment_item_id == item.id,
                EnrichmentItemData.deleted_at.is_(None),
            )
        ).all()
        item_data_map[item.id] = item_data

    add_enrichment_item_data = []
    for old_item, new_item in zip(enrichment_items, add_enrichment_item):
        for item_data in item_data_map.get(old_item.id, []):
            new_item_data = EnrichmentItemData(
                enrichment_item_id=new_item.id,
                column_json_mapping_id=item_data.column_json_mapping_id,
                value=item_data.value,
                created_by=user_id,
                updated_by=user_id,
            )
            add_enrichment_item_data.append(new_item_data)

    db.add_all(add_enrichment_item_data)
    db.commit()
    db.refresh(new_enrichment)

    return get_enrichment(db, new_enrichment.id, team_id, listing_plan_code)


def update_enrichment_status(db: Session, enrichment_id: int, team_id: int):
    enrichment = db.exec(
        select(Enrichment).where(
            Enrichment.id == enrichment_id,
            Enrichment.team_id == team_id,
            Enrichment.deleted_at.is_(None),
        )
    ).first()
    if not enrichment:
        raise NotFoundException(detail="enrichments.enrichmentNotFound")
    enrichment.status = EnrichmentStatus.BEING_IDENTIFIED
    db.add(enrichment)
    enrichment_items = db.exec(
        select(EnrichmentItem).where(
            EnrichmentItem.enrichment_id == enrichment.id,
            EnrichmentItem.deleted_at.is_(None),
        )
    ).all()
    for item in enrichment_items:
        item.status = EnrichmentStatus.BEING_IDENTIFIED
        item.entity_identifier = None
        db.add(item)
    db.commit()
    db.refresh(enrichment)
    return enrichment


def convert_dot_columns_to_underscore(columns):
    return [re.sub(r"\.(\d+)$", r"_\1", col) for col in columns]


async def verify_enrichment_file(
    enrichment_id: int,
    file: UploadFile,
    db: Session,
) -> EnrichmentVerifyFileResponse:

    enrichment = db.exec(
        select(Enrichment).where(
            Enrichment.id == enrichment_id,
            Enrichment.deleted_at.is_(None),
        )
    ).first()
    if not enrichment:
        raise NotFoundException(detail="common.notFound")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="uploadfile.incorrectFormat")

    # Read file content
    content = await file.read(MAX_FILE_SIZE_BYTES + 1)

    # Check file size
    file_size = len(content)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"uploadfile.fileTooLarge",
        )
    encoding = chardet.detect(content)["encoding"]
    text_content = content.decode(encoding, "replace")
    row_count = text_content.count("\n")
    if row_count > 0:
        row_count -= 1  # Trừ header
    if row_count > 10000:
        raise HTTPException(
            status_code=400,
            detail="uploadfile.exceedEnrichmentItem",
        )
    df_header = pd.read_csv(io.StringIO(text_content), nrows=0)
    df_header.columns = convert_dot_columns_to_underscore(df_header.columns.tolist())
    is_compatible = file_compatible_check(df_header.columns.tolist(), enrichment_id, db)
    if not is_compatible:
        raise HTTPException(
            status_code=400,
            detail="uploadfile.incompatibleColumns",
        )
    result = EnrichmentVerifyFileResponse(
        is_compatible=True if is_compatible else False,
        total_columns=len(df_header.columns),
        total_rows=row_count,
    )
    return result


def update_enrichment_item_data(
    db: Session,
    overwrite_rows_ids: List,
    data_map: Dict,
):
    overwrite_rows_data_query = select(EnrichmentItemData).where(
        EnrichmentItemData.enrichment_item_id.in_(overwrite_rows_ids),
        EnrichmentItemData.deleted_at.is_(None),
    )
    overwrite_rows_data = db.exec(overwrite_rows_data_query).all()
    for item_data in overwrite_rows_data:
        if item_data.enrichment_item_id in data_map:
            item_data.value = str(
                data_map[item_data.enrichment_item_id][item_data.column_json_mapping_id]
            )
    db.add_all(overwrite_rows_data)
    db.flush()


async def upload_enrichment_csv_file(
    db: Session,
    file: UploadFile,
    team_id: int,
    user_id: int,
    encoding: Optional[EnrichmentFileEncoding] = EnrichmentFileEncoding.UTF_8,
    delimiter: Optional[EnrichmentFileDelimiter] = EnrichmentFileDelimiter.COMMA,
    column_json_mapping: Optional[str] = "{}",
    enrichment_id: Optional[int] = None,
    method: Optional[EnrichmentUploadFileMethod] = None,
):
    """Upload an enrichment CSV file and create an enrichment item per row."""
    encoding_map = {
        "UTF_8": "utf-8",
        "SHIFT_JIS": "SHIFT_JIS",
    }
    delimiter_map = {
        "COMMA": ",",
        "TAB": "\t",
    }

    try:
        column_json_mapping_dict = json.loads(column_json_mapping)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON format in column_json_mapping"
        )
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="uploadfile.incorrectFormat")
    content = await file.read()
    enrichment_item_count = 0
    if enrichment_id:
        column_json_mapping_dict = db.exec(
            select(Enrichment.column_json_mapping).where(
                Enrichment.id == enrichment_id,
                Enrichment.deleted_at.is_(None),
            )
        ).first()
        enrichment_item_count = db.exec(
            select(func.count(EnrichmentItem.id)).where(
                EnrichmentItem.enrichment_id == enrichment_id,
                EnrichmentItem.deleted_at.is_(None),
            )
        ).first()

    # Tối ưu: Chỉ detect encoding trên 50KB đầu tiên thay vì toàn bộ file
    # Điều này giảm đáng kể CPU load với file lớn
    sample_size = min(50000, len(content))
    result = chardet.detect(content[:sample_size])["encoding"]
    if result not in ["utf-8", "SHIFT_JIS"]:
        raise HTTPException(status_code=400, detail="uploadfile.unsupportedEncoding")
    if result != encoding_map[encoding.value]:
        raise HTTPException(status_code=400, detail="uploadfile.encodingMismatch")
    try:
        text_content = content.decode(encoding_map[encoding.value], "replace")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"uploadfile.failedToDecode",
        )

    df_header = pd.read_csv(
        io.StringIO(text_content),
        sep=delimiter_map[delimiter.value],
        nrows=0,  # Chỉ đọc header, không load data
        index_col=False,
    )

    # Tối ưu: Đếm dòng hiệu quả hơn bằng cách đếm trên bytes thay vì string
    # Bytes count nhanh hơn string count
    row_count = content.count(b"\n")
    if row_count > 0:
        row_count -= 1  # Trừ header

    if row_count + enrichment_item_count > 10000:
        raise HTTPException(
            status_code=400,
            detail="uploadfile.exceedEnrichmentItem",
        )
    enrichment = None
    if enrichment_id:
        enrichment = file_compatible_check(
            df_header.columns.tolist(), enrichment_id, db
        )
        if not enrichment:
            raise HTTPException(
                status_code=400,
                detail="uploadfile.incompatibleColumns",
            )
        db.exec(
            update(Enrichment)
            .where(Enrichment.id == enrichment_id)
            .values(status=EnrichmentStatus.BEING_IDENTIFIED)
            .returning(Enrichment)
        ).first()

    else:
        enrichment_names = db.exec(
            select(Enrichment.name).where(
                Enrichment.team_id == team_id,
                Enrichment.deleted_at.is_(None),
            )
        ).all()
        unique_name = get_unique_name(
            file.filename.rsplit(".", 1)[0], enrichment_names, ext_name=False
        )
        enrichment = Enrichment(
            name=unique_name,
            type=EnrichmentType.CPN,
            team_id=team_id,
            column_json_mapping=column_json_mapping_dict,
            status=EnrichmentStatus.BEING_IDENTIFIED,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(enrichment)
        db.flush()
    enrichment_files = db.exec(
        select(EnrichmentFile.file_name).where(
            EnrichmentFile.enrichment_id == enrichment.id,
            EnrichmentFile.deleted_at.is_(None),
        )
    ).all()
    unique_name = get_unique_name(file.filename, enrichment_files)
    try:
        s3_object_key = save_file_to_s3(file, enrichment.id)
    except Exception as e:
        print(f"Failed to save file to S3: {e}")
        raise HTTPException(status_code=500, detail="common.uploadFileFailed")
    enrichment_file = EnrichmentFile(
        enrichment_id=enrichment.id,
        file_name=unique_name,
        s3_object_key=s3_object_key,
        upload_process_status=UploadProcessStatus.IN_PROGRESS.value,
        encoding=encoding,
        delimiter=delimiter,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(enrichment_file)
    db.flush()
    enrichment_id = enrichment.id
    enrichment_file_id = enrichment_file.id
    db.commit()

    upload_enrichment_item_from_file.apply_async(
        (
            enrichment_id,
            enrichment_file_id,
            user_id,
            column_json_mapping_dict,
            delimiter.value,
            method.value if method else None,
        ),
    )

    db.refresh(enrichment)
    return {
        "enrichment": enrichment,
        "total_rows": 0,
        "total_columns": 0,
    }


def select_identified_items(
    db: Session,
    enrichment_id: int,
    team_id: int,
    current_page: bool,
    page: int,
    per_page: int,
    total: int,
) -> List[str]:

    enrichment = db.exec(
        select(Enrichment).where(
            Enrichment.id == enrichment_id,
            Enrichment.team_id == team_id,
            Enrichment.deleted_at.is_(None),
        )
    ).first()

    if not enrichment:
        raise NotFoundException(detail="enrichments.enrichmentNotFound")

    enrichment_items_id = db.exec(
        select(EnrichmentItem.id)
        .where(
            EnrichmentItem.enrichment_id == enrichment_id,
            EnrichmentItem.deleted_at.is_(None),
            EnrichmentItem.entity_identifier.is_not(None),
        )
        .order_by(EnrichmentItem.id.asc())
    ).all()

    if current_page:
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, len(enrichment_items_id))

        return enrichment_items_id[start_idx:end_idx]
    else:
        return enrichment_items_id[: min(total, len(enrichment_items_id))]


def get_corporate_number_by_item_id(
    db: Session,
    enrichment_id: int,
    listing_plan_code: PlanCode,
    current_user: UserBase,
    item_ids: List[int],
):
    query = (
        select(
            EnrichmentItem.entity_identifier,
            func.count(EnrichmentItem.id).label("total_identified"),
            func.count(
                case(
                    (
                        TeamCompany.corporate_number.is_not(None),
                        TeamCompany.corporate_number,
                    ),
                    else_=None,
                )
            ).label("total_unlock"),
        )
        .outerjoin(
            TeamCompany,
            (TeamCompany.corporate_number == EnrichmentItem.entity_identifier)
            & (TeamCompany.team_id == current_user.team_id),
        )
        .where(
            EnrichmentItem.enrichment_id == enrichment_id,
            EnrichmentItem.deleted_at.is_(None),
            EnrichmentItem.entity_identifier.is_not(None),
            EnrichmentItem.id.in_(item_ids) if item_ids else True,
        )
        .group_by(EnrichmentItem.entity_identifier)
    )

    result = db.exec(query).all()

    if not result:
        raise NotFoundException(detail="enrichments.corporateNumberNotFound")

    total = len(item_ids) if item_ids else 0
    corporate_numbers = [r.entity_identifier for r in result]
    total_identified = sum(r.total_identified for r in result)
    total_unlock = sum(r.total_unlock for r in result)

    if listing_plan_code == PlanCode.UNLIMITED:
        return {
            "total": total,
            "total_lock": 0,
            "total_unlock": total_identified,
            "total_identified": total_identified,
            "corporate_numbers": corporate_numbers,
        }

    return {
        "total": total,
        "total_lock": total_identified - total_unlock,
        "total_unlock": total_unlock,
        "total_identified": total_identified,
        "corporate_numbers": corporate_numbers,
    }


def get_entity_identifier_by_enrichment_id(
    db: Session, current_user: UserBase, enrichment_ids: List[int]
) -> CorporateNumberByIdentified:
    query = (
        select(EnrichmentItem.entity_identifier)
        .join(Enrichment, EnrichmentItem.enrichment_id == Enrichment.id)
        .where(
            Enrichment.id.in_(enrichment_ids),
            Enrichment.deleted_at.is_(None),
            Enrichment.team_id == current_user.team_id,
            EnrichmentItem.deleted_at.is_(None),
            EnrichmentItem.entity_identifier.is_not(None),
        )
    )

    entity_identifiers = db.exec(query).all()

    return CorporateNumberByIdentified(or_corporate_numbers=entity_identifiers)
