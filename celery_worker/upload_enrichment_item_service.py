# flake8: noqa: E501
import gc
import re
import time
from io import BytesIO
from typing import Dict, Optional

# from sqlalchemy import select, join
import pandas as pd
from sqlalchemy.orm import aliased
from sqlmodel import Session, and_, delete, func, select, update

from app.models.enrichment import (
    Enrichment,
    EnrichmentStatus,
    EnrichmentUploadFileMethod,
)
from app.models.enrichment_file import EnrichmentFile, EnrichmentFileDelimiter
from app.models.enrichment_item import EnrichmentItem
from app.models.enrichment_item_data import EnrichmentItemData
from app.models.sequence.campaign_import import UploadProcessStatus
from utils.enrichment.delete_enrichment_service import delete_all_file_in_enrichment
from utils.enrichment.extract_domain import extract_domain
from utils.enrichment.s3 import get_file_from_s3
from utils.enrichment.utils import file_compatible_check

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def upload_enrichment_item_from_file_service(
    enrichment_id: int,
    enrichment_file_id: int,
    user_id: int,
    column_json_mapping_dict: dict,
    db: Session,
    delimiter: EnrichmentFileDelimiter = EnrichmentFileDelimiter.COMMA,
    method: EnrichmentUploadFileMethod = None,
):
    print(f"Start task upload enrichment item from file {enrichment_file_id}")
    try:
        enrichment_file = db.exec(
            select(EnrichmentFile).where(EnrichmentFile.id == enrichment_file_id)
        ).first()
        if not enrichment_file:
            print(
                f"Enrichment file not found for enrichment_file_id {enrichment_file_id}"
            )
            return None
        file_content = get_file_from_s3(enrichment_id, enrichment_file.s3_object_key)
        if not file_content:
            raise Exception("File content is empty or could not be retrieved")
    except Exception as e:
        print(f"Failed to get file from S3: {e}")
        db.exec(
            update(EnrichmentFile)
            .where(EnrichmentFile.id == enrichment_file_id)
            .values(upload_process_status=UploadProcessStatus.FAILED.value)
        )
        return None
    file_size = len(file_content)
    print(f"File size: {file_size}")
    if file_size > MAX_FILE_SIZE_BYTES:
        print(f"File size is too large: {file_size}")
        db.exec(
            update(EnrichmentFile)
            .where(EnrichmentFile.id == enrichment_file_id)
            .values(upload_process_status=UploadProcessStatus.FAILED.value)
        )
        db.exec(
            update(Enrichment)
            .where(Enrichment.id == enrichment_id)
            .values(status=EnrichmentStatus.FAILED)
        )
        return None

    file_like = BytesIO(file_content)

    # if method:
    #     df_check = pd.read_csv(file_like, delimiter=delimiter)
    #     enrichment = file_compatible_check(
    #         df_check.columns.tolist(), enrichment_id, db
    #     )
    #     if not enrichment:
    #         print(f"Enrichment file not compatible with enrichment {enrichment_id}")
    #         db.exec(
    #             update(EnrichmentFile)
    #             .where(EnrichmentFile.id == enrichment_file_id)
    #             .values(upload_process_status=UploadProcessStatus.FAILED.value)
    #         )
    #         db.exec(
    #             update(Enrichment)
    #             .where(Enrichment.id == enrichment_id)
    #             .values(status=EnrichmentStatus.FAILED)
    #         )
    #         return None
    #     db.exec(
    #         update(Enrichment)
    #         .where(Enrichment.id == enrichment_id)
    #         .values(status=EnrichmentStatus.BEING_IDENTIFIED)
    #     )
    #     file_like.seek(0)
    delimiter_map = {
        "COMMA": ",",
        "TAB": "\t",
    }
    df = pd.read_csv(file_like, sep=delimiter_map[delimiter], on_bad_lines="skip")
    df = clean_data(df)
    if method == EnrichmentUploadFileMethod.OVERWRITE:
        delete_all_file_in_enrichment(enrichment_id, db)
    elif method == EnrichmentUploadFileMethod.ADD_NEW:
        duplicated_item_list = exsisted_enrichment_item(
            db,
            enrichment_id,
            column_json_mapping_dict,
            df,
        )
        df = df.drop(duplicated_item_list)
        df = df.reset_index(drop=True)
    result = add_item_from_enrichment_file(
        enrichment_id,
        enrichment_file_id,
        df,
        user_id,
        column_json_mapping_dict,
        db,
    )

    print(f"Finish task upload enrichment item from file {enrichment_file_id}")
    return result


def exsisted_enrichment_item(
    db: Session,
    enrichment_id: int,
    column_json_mapping: Dict,
    df: pd.DataFrame,
):

    # Step 1: Lấy danh sách enrichment items (chỉ lấy ID, không load hết data)
    items_query = select(EnrichmentItem.id).where(
        EnrichmentItem.enrichment_id == enrichment_id,
        EnrichmentItem.deleted_at.is_(None),
    )

    enrichment_item_ids = db.exec(items_query).all()

    if not enrichment_item_ids:
        return []

    # Step 2: Lấy data nhưng chỉ các columns cần thiết để so sánh
    data_query = (
        select(
            EnrichmentItemData.enrichment_item_id,
            EnrichmentItemData.column_json_mapping_id,
            EnrichmentItemData.value,
        )
        .where(
            EnrichmentItemData.enrichment_item_id.in_(enrichment_item_ids),
            EnrichmentItemData.deleted_at.is_(None),
        )
        .order_by(
            EnrichmentItemData.enrichment_item_id,
            EnrichmentItemData.column_json_mapping_id,
        )
    )

    enrichment_data = db.exec(data_query).all()

    # Step 3: Build signature map (tối ưu hơn)
    signature_map = {}
    current_item_id = None
    current_values = {}

    for data in enrichment_data:
        if current_item_id != data.enrichment_item_id:
            # Save previous item signature
            if current_item_id is not None:
                signature = tuple(
                    current_values.get(int(label_id), "")
                    for label_id in column_json_mapping.keys()
                )
                if signature not in signature_map:
                    signature_map[signature] = []
                signature_map[signature].append(current_item_id)

            # Start new item
            current_item_id = data.enrichment_item_id
            current_values = {}

        current_values[data.column_json_mapping_id] = data.value or ""

    # Don't forget last item
    if current_item_id is not None:
        signature = tuple(
            current_values.get(int(label_id), "")
            for label_id in column_json_mapping.keys()
        )
        if signature not in signature_map:
            signature_map[signature] = []
        signature_map[signature].append(current_item_id)

    # Step 4: So sánh với DataFrame
    is_overwrite = []

    for index, row in df.iterrows():
        # Tạo signature từ row
        values = []
        for label_id in column_json_mapping.keys():
            value = row[int(label_id)]
            if pd.notna(value) and str(value).strip() != "":
                values.append(str(value))
            else:
                values.append("")

        signature = tuple(values)

        # Check nếu signature này đã tồn tại
        if signature in signature_map:
            is_overwrite.append(index)

    return is_overwrite


def clean_data(
    df: pd.DataFrame,
    column_json_mapping: Optional[Dict] = None,
) -> pd.DataFrame:
    """Clean the DataFrame by stripping whitespace and dropping empty rows."""
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.dropna(how="all")
    df = df[~df.apply(lambda row: all((v == "" or pd.isna(v)) for v in row), axis=1)]
    df = df.where(pd.notna(df), "")
    new_columns = [
        (
            f"列{idx+1}"
            if not col
            or str(col).strip() == ""
            or str(col).lower().startswith("unnamed")
            else col
        )
        for idx, col in enumerate(df.columns)
    ]
    final_columns = []

    def normalize_phone(phone: str) -> str:
        if not isinstance(phone, str):
            return phone
        # Xoá tất cả ký tự không phải số
        digits = re.sub(r"\D", "", phone)
        # Nếu bắt đầu bằng '81' (mã Nhật), đổi thành '0'
        if digits.startswith("81") and len(digits) >= 11:
            digits = "0" + digits[2:]
        # Nếu bắt đầu bằng '0' và đủ 11 số, giữ nguyên
        if digits.startswith("0") and len(digits) == 11:
            return digits
        # Nếu đủ 11 số, trả về
        if len(digits) == 11:
            return digits
        return digits

    # def normalize_domain(domain: str) -> str:
    #     if not isinstance(domain, str):
    #         return domain
    #     # Bỏ http:// hoặc https://
    #     domain = re.sub(r"^https?://", "", domain, flags=re.IGNORECASE)
    #     # Bỏ www.
    #     domain = re.sub(r"^www\.", "", domain, flags=re.IGNORECASE)
    #     # Lấy domain chính (bỏ subdomain)
    #     domain = domain.split("/")[0]
    #     return domain

    def normalize_email(email: str) -> str:
        if not isinstance(email, str):
            return email
        # Loại bỏ khoảng trắng, chuyển về chữ thường
        email = email.strip().lower()
        # Loại bỏ các ký tự không hợp lệ ở đầu/cuối
        email = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", email)
        return email

    def fix_duplicate(col):
        m = re.match(r"^(.*)\.(\d+)$", col)
        if m:
            return f"{m.group(1)}_{m.group(2)}"
        return col

    final_columns = [fix_duplicate(col) for col in new_columns]
    df.columns = final_columns

    if column_json_mapping:
        phone_columns = [
            v["upload_column"]
            for v in column_json_mapping.values()
            if v.get("service_column") == "phone"
        ]
        for col in phone_columns:
            if col in df.columns:
                df[col] = df[col].apply(normalize_phone)
        # Tìm tên cột upload_column có service_column là 'domain'
        domain_columns = [
            v["upload_column"]
            for v in column_json_mapping.values()
            if v.get("service_column") == "domain"
        ]
        for col in domain_columns:
            if col in df.columns:
                df[col] = df[col].apply(extract_domain)
        email_columns = [
            v["upload_column"]
            for v in column_json_mapping.values()
            if v.get("service_column") == "contact_email"
            or v.get("service_column") == "recruit_email"
        ]
        for col in email_columns:
            if col in df.columns:
                df[col] = df[col].apply(normalize_email)

        # Bỏ các hàng không có dữ liệu ở cả 3 cột: name, corporate_number và domain
        name_columns = [
            v["upload_column"]
            for v in column_json_mapping.values()
            if v.get("service_column") == "name"
        ]
        corporate_number_columns = [
            v["upload_column"]
            for v in column_json_mapping.values()
            if v.get("service_column") == "corporate_number"
        ]

        # Lấy các cột cần kiểm tra (name, corporate_number, domain)
        check_columns = []
        for col in name_columns + corporate_number_columns + domain_columns:
            if col in df.columns:
                check_columns.append(col)

        if check_columns:
            # Lọc các hàng có ít nhất 1 trong 3 cột có dữ liệu
            df = df[
                df[check_columns].apply(
                    lambda row: any(
                        (str(v).strip() != "" and not pd.isna(v)) for v in row
                    ),
                    axis=1,
                )
            ]

    df = df.drop_duplicates(keep="first")
    return df


def add_item_from_enrichment_file(
    enrichment_id: int,
    enrichment_file_id: int,
    df: Dict,
    user_id: int,
    column_json_mapping_dict: Dict,
    db: Session,
):
    print(
        f"[add_item_from_enrichment_file] Start processing enrichment_file_id={enrichment_file_id}"
    )
    overall_start = time.time()

    df = pd.DataFrame(df)
    enrichment_item_and_data = []
    enrichment_items = []

    prepare_start = time.time()
    for index, row in df.iterrows():
        enrichment_item = EnrichmentItem(
            enrichment_id=enrichment_id,
            enrichment_file_id=enrichment_file_id,
            status=EnrichmentStatus.BEING_IDENTIFIED,
            created_by=user_id,
            updated_by=user_id,
        )
        enrichment_items.append(enrichment_item)
        enrichment_item_and_data.append(
            {
                "enrichment_item": enrichment_item,
                "row": row,
            }
        )
    prepare_time = time.time() - prepare_start
    print(
        f"[add_item_from_enrichment_file] Prepared {len(enrichment_items)} items in {prepare_time:.3f}s"
    )

    # Insert enrichment items
    insert_items_start = time.time()
    print(
        f"[add_item_from_enrichment_file] Starting db.add_all for {len(enrichment_items)} EnrichmentItems..."
    )
    db.add_all(enrichment_items)
    db.flush()
    insert_items_time = time.time() - insert_items_start
    print(
        f"[add_item_from_enrichment_file] db.add_all + flush for EnrichmentItems completed in {insert_items_time:.3f}s"
    )

    # Insert enrichment item data với BATCH để giảm memory
    insert_data_start = time.time()
    print(f"[add_item_from_enrichment_file] Starting to insert EnrichmentItemData...")

    BATCH_SIZE = 1000  # Insert 1000 items 1 lần để giảm memory
    batch_item_data_list = []
    total_inserted = 0

    for idx, enrichment_item_data in enumerate(enrichment_item_and_data):
        enrichment_item = enrichment_item_data["enrichment_item"]
        row = enrichment_item_data["row"]

        item_data_list = [
            EnrichmentItemData(
                enrichment_item_id=enrichment_item.id,
                column_json_mapping_id=column_json_mapping_id,
                value=str(value) if value is not None and value != "" else None,
                created_by=user_id,
                updated_by=user_id,
            )
            for column_json_mapping_id, value in enumerate(row.tolist())
        ]
        batch_item_data_list.extend(item_data_list)

        # Insert khi đủ batch hoặc là item cuối cùng
        if (
            len(batch_item_data_list) >= BATCH_SIZE
            or idx == len(enrichment_item_and_data) - 1
        ):
            db.add_all(batch_item_data_list)
            db.flush()  # Flush để giải phóng memory
            total_inserted += len(batch_item_data_list)
            print(
                f"[add_item_from_enrichment_file] Inserted batch: {len(batch_item_data_list)} items (Total: {total_inserted})"
            )

            # Giải phóng memory
            batch_item_data_list.clear()
            gc.collect()

    insert_data_time = time.time() - insert_data_start
    print(
        f"[add_item_from_enrichment_file] Completed inserting {total_inserted} items in {insert_data_time:.3f}s"
    )
    commit_start = time.time()
    print(f"[add_item_from_enrichment_file] Starting first db.commit()...")
    db.commit()
    commit_time = time.time() - commit_start
    print(
        f"[add_item_from_enrichment_file] First db.commit() completed in {commit_time:.3f}s"
    )

    # Query EnrichmentFile with FOR UPDATE lock
    # lock_start = time.time()
    # print(
    #     f"[add_item_from_enrichment_file] Acquiring FOR UPDATE lock for enrichment_file_id={enrichment_file_id}..."
    # )

    enrichment_file = db.exec(
        update(EnrichmentFile)
        .where(EnrichmentFile.id == enrichment_file_id)
        .values(upload_process_status=UploadProcessStatus.FINISHED.value)
    )

    # lock_time = time.time() - lock_start
    # if lock_time > 1:
    #     print(
    #         f"[add_item_from_enrichment_file] FOR UPDATE lock acquired in {lock_time:.3f}s (SLOW - waited for lock)"
    #     )
    # else:
    #     print(
    #         f"[add_item_from_enrichment_file] FOR UPDATE lock acquired in {lock_time:.3f}s"
    #     )

    handle_identify = True
    # if enrichment_file.upload_process_status != UploadProcessStatus.FINISHED.value:
    #     # Count existing items
    #     count_start = time.time()
    #     print(f"[add_item_from_enrichment_file] Querying count of EnrichmentItems...")
    #     result = db.exec(
    #         select(func.count(EnrichmentItem.id)).where(
    #             EnrichmentItem.enrichment_file_id == enrichment_file_id,
    #             EnrichmentItem.deleted_at.is_(None),
    #         )
    #     ).first()
    #     count_time = time.time() - count_start
    #     item_count = result if isinstance(result, int) else result[0]
    #     print(
    #         f"[add_item_from_enrichment_file] Count query completed in {count_time:.3f}s, item_count={item_count}, expected_total={total}"
    #     )

    #     if item_count == total:
    #         enrichment_file.upload_process_status = UploadProcessStatus.FINISHED.value
    #         handle_identify = True
    #         print(
    #             f"[add_item_from_enrichment_file] Upload completed! Setting status to FINISHED and handle_identify=True"
    #         )

    final_commit_start = time.time()
    print(f"[add_item_from_enrichment_file] Starting final db.commit()...")
    db.commit()
    final_commit_time = time.time() - final_commit_start
    print(
        f"[add_item_from_enrichment_file] Final db.commit() completed in {final_commit_time:.3f}s"
    )

    overall_time = time.time() - overall_start
    print(
        f"[add_item_from_enrichment_file] COMPLETED for enrichment_file_id={enrichment_file_id} in {overall_time:.3f}s total"
    )

    # Explicitly giải phóng bộ nhớ trước khi return
    del df
    del enrichment_items
    del enrichment_item_and_data
    gc.collect()
    print(f"[add_item_from_enrichment_file] Memory cleaned before return")

    return {"handle_identify": handle_identify}
