# flake8: noqa: E501
import gc
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import tldextract
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import aliased
from sqlmodel import Session, and_, case, func, or_, select, text, tuple_, update

from app.db import engine
from app.models.company import Company
from app.models.enrichment import Enrichment, EnrichmentStatus, EnrichmentType
from app.models.enrichment_item import EnrichmentItem
from app.models.enrichment_item_data import EnrichmentItemData
from utils.identify.utils import normalize_company_name


def extract_domain(hp_url):
    if not hp_url:
        return None
    extract = tldextract.extract(hp_url)
    if not extract.suffix:
        if not extract.domain:
            return None
        return extract.domain
    if not extract.domain:
        return extract.suffix
    return f"{extract.domain}.{extract.suffix}"


def identify_enrichment_file(
    db: Session,
    enrichment: Enrichment,
    user_id: int,
    enrichment_items: Optional[List[EnrichmentItem]] = None,
    is_last_chunk: Optional[bool] = None,
    enrichment_file_id: Optional[int] = None,
):
    # db.execute(text("SET statement_timeout = 590000"))
    try:
        BATCH_SIZE = 250
        column_json_mapping = enrichment.column_json_mapping

        # Query 1: Lấy danh sách enrichment items với pagination (tối ưu hơn)
        count_query = select(func.count(EnrichmentItem.id)).where(
            EnrichmentItem.enrichment_id == enrichment.id,
            EnrichmentItem.deleted_at.is_(None),
        )

        if enrichment_file_id:
            count_query = count_query.where(
                EnrichmentItem.enrichment_file_id == enrichment_file_id
            )

        items_count = db.exec(count_query).first()
        if items_count == 0:
            print(f"No enrichment items found for enrichment {enrichment.id}")
            if enrichment.status != EnrichmentStatus.FAILED:
                enrichment.status = EnrichmentStatus.IDENTIFIED
            enrichment.updated_at = datetime.now()
            enrichment.updated_by = user_id
            db.add(enrichment)
            db.commit()
            return

        print(f"Total items to identify: {items_count}")

        for i in range(0, items_count, BATCH_SIZE):
            # Tạo items_query mới cho mỗi batch
            items_query = (
                select(EnrichmentItem)
                .where(
                    EnrichmentItem.enrichment_id == enrichment.id,
                    EnrichmentItem.deleted_at.is_(None),
                )
                .order_by(EnrichmentItem.id)
                .offset(i)
                .limit(BATCH_SIZE)
            )

            if enrichment_file_id:
                items_query = items_query.where(
                    EnrichmentItem.enrichment_file_id == enrichment_file_id
                )

            enrichment_items = db.exec(items_query).all()

            # Query 2: Lấy data cho các items (tách riêng để tối ưu)
            item_ids = [item.id for item in enrichment_items]
            data_query = (
                select(EnrichmentItemData)
                .where(
                    EnrichmentItemData.enrichment_item_id.in_(item_ids),
                    EnrichmentItemData.deleted_at.is_(None),
                )
                .order_by(
                    EnrichmentItemData.enrichment_item_id,
                    EnrichmentItemData.column_json_mapping_id,
                )
            )

            enrichment_data = db.exec(data_query).all()

            # Tạo mapping từ data
            data_map = {}
            for data in enrichment_data:
                if data.enrichment_item_id not in data_map:
                    data_map[data.enrichment_item_id] = {}
                data_map[data.enrichment_item_id][
                    data.column_json_mapping_id
                ] = data.value

            # Kết hợp items với data thành dict format
            enrichment_item_list = []
            for item in enrichment_items:
                item_data = data_map.get(item.id, {})

                # Tạo dict với structure tương thích với code cũ
                item_dict = {0: item}  # item[0] sẽ trả về enrichment_item

                # Thêm các label values
                for label_id in column_json_mapping.keys():
                    value = item_data.get(int(label_id), "")
                    item_dict[f"label_{label_id}"] = value

                enrichment_item_list.append(item_dict)
            mapping_id_to_service_col = {
                str(k): v["service_column"]
                for k, v in enrichment.column_json_mapping.items()
            }
            mapping_service_col_to_id = {
                v["service_column"]: str(k)
                for k, v in enrichment.column_json_mapping.items()
            }
            standardized = (
                # lambda x, y: extract_domain(x)
                # if y == "domain"
                # else normalize_company_name(x)
                # if y == "name"
                # else x
                lambda x, y: x
            )
            company_attr_mapping = {
                "corporate_number": "corporate_number",
                "name": "name",
                "domain": "domain",
                "normalized_name": "normalized_name",
            }
            print(
                f"Start identify enrichment {enrichment.id}, batch {i // BATCH_SIZE + 1}, batch size: {BATCH_SIZE}"
            )
            batch = enrichment_item_list
            print(f"Processing {len(batch)} items in this batch")
            data_list = ["corporate_number", "domain", "name", "normalized_name"]
            if enrichment.type == EnrichmentType.CPN:
                failed_item_ids = []
                identified_item_ids = []
                entity_map = {}
                mapping_company_list = {
                    "corporate_number": {},
                    "name": {},
                    "domain": {},
                    "normalized_name": {},
                }

                print(f"[Optimization] Building combined query conditions...")

                all_conditions = []

                # Collect all values for each field using single loop
                for col_name in data_list:
                    # Skip normalized_name nếu name không tồn tại
                    if col_name == "normalized_name":
                        if "name" not in mapping_service_col_to_id:
                            continue
                        # normalized_name derives from name
                        field_id = mapping_service_col_to_id["name"]
                        values = [
                            normalize_company_name(item[f"label_{field_id}"])
                            for item in batch
                            if item.get(f"label_{field_id}")
                        ]
                    else:
                        # Regular columns: corporate_number, domain, name
                        if col_name not in mapping_service_col_to_id:
                            continue
                        field_id = mapping_service_col_to_id[col_name]
                        values = [
                            standardized(item[f"label_{field_id}"], col_name)
                            for item in batch
                            if item.get(f"label_{field_id}")
                        ]

                    # Filter out None/empty values
                    values = [v for v in values if v]

                    if values:
                        # Add condition for this column
                        company_attr = company_attr_mapping[col_name]
                        all_conditions.append(
                            getattr(Company, company_attr).in_(values)
                        )
                        print(f"  - {len(values)} {col_name}(s)")

                if all_conditions:
                    query_start = time.time()

                    query = select(
                        Company.id,
                        Company.corporate_number,
                        Company.name,
                        Company.domain,
                        Company.normalized_name,
                    ).where(Company.nta_closed_date.is_(None), or_(*all_conditions))

                    print(f"[Optimization] Executing SINGLE combined query...")
                    print(f"[Optimization] Query: {query}")
                    company_list = db.exec(query).all()
                    query_time = time.time() - query_start

                    print(
                        f"[Optimization] ✅ Found {len(company_list)} companies in {query_time:.3f}s (SINGLE query)"
                    )

                    # Build mapping from results
                    for company in company_list:
                        company_tuple = (company.id, company.corporate_number)

                        # Map name - no duplicate check needed, just append
                        if company.name:
                            if company.name not in mapping_company_list["name"]:
                                mapping_company_list["name"][company.name] = []
                            mapping_company_list["name"][company.name].append(
                                company_tuple
                            )

                        # Map corporate_number
                        if company.corporate_number:
                            if (
                                company.corporate_number
                                not in mapping_company_list["corporate_number"]
                            ):
                                mapping_company_list["corporate_number"][
                                    company.corporate_number
                                ] = []
                            mapping_company_list["corporate_number"][
                                company.corporate_number
                            ].append(company_tuple)

                        # Map domain
                        if company.domain:
                            if company.domain not in mapping_company_list["domain"]:
                                mapping_company_list["domain"][company.domain] = []
                            mapping_company_list["domain"][company.domain].append(
                                company_tuple
                            )

                        # Map normalized_name
                        if company.normalized_name:
                            if (
                                company.normalized_name
                                not in mapping_company_list["normalized_name"]
                            ):
                                mapping_company_list["normalized_name"][
                                    company.normalized_name
                                ] = []
                            mapping_company_list["normalized_name"][
                                company.normalized_name
                            ].append(company_tuple)
                else:
                    print(f"[Optimization] No conditions to query, skipping...")

                # Deduplicate all lists to avoid duplicate companies
                for field_name in mapping_company_list:
                    for key in mapping_company_list[field_name]:
                        # Convert to list of unique tuples (preserve order)
                        seen = set()
                        unique_list = []
                        for item in mapping_company_list[field_name][key]:
                            if item not in seen:
                                seen.add(item)
                                unique_list.append(item)
                        mapping_company_list[field_name][key] = unique_list

                print(
                    f"Mapping completed: {len(mapping_company_list)} companies mapped"
                )
                identified_item_ids, entity_map, failed_item_ids = matching_company(
                    batch=batch,
                    mapping_company_list=mapping_company_list,
                    column_json_mapping=column_json_mapping,
                    mapping_id_to_service_col=mapping_id_to_service_col,
                    db=db,
                )
                if identified_item_ids:
                    stmt = (
                        update(EnrichmentItem)
                        .where(EnrichmentItem.id.in_(identified_item_ids))
                        .values(
                            entity_identifier=case(
                                [
                                    (EnrichmentItem.id == k, v)
                                    for k, v in entity_map.items()
                                ],
                                else_=None,
                            ),
                            status=EnrichmentStatus.IDENTIFIED,
                            updated_at=datetime.now(),
                            updated_by=user_id,
                        )
                    )
                    db.exec(stmt)
                if failed_item_ids:
                    stmt = (
                        update(EnrichmentItem)
                        .where(EnrichmentItem.id.in_(failed_item_ids))
                        .values(
                            status=EnrichmentStatus.IDENTIFIED,
                            updated_at=datetime.now(),
                            updated_by=user_id,
                        )
                    )
                    db.exec(stmt)
                db.commit()

                # Explicitly giải phóng bộ nhớ sau mỗi batch
                del mapping_company_list
                del entity_map
                del identified_item_ids
                del failed_item_ids
                del batch
                del enrichment_item_list
                # Expunge tất cả objects (bao gồm cả enrichment)
                db.expunge_all()

                # Re-merge enrichment object vào session để có thể update sau này
                # merge(load=False) không query lại DB, chỉ re-attach object
                enrichment = db.merge(enrichment, load=False)

                del enrichment_items
                del enrichment_data
                del data_map

                gc.collect()
                print(f"✅ Memory cleaned after batch {i // BATCH_SIZE + 1}")

        if is_last_chunk is None or is_last_chunk is True:
            if enrichment.status != EnrichmentStatus.FAILED:
                enrichment.status = EnrichmentStatus.IDENTIFIED
            enrichment.updated_at = datetime.now()
            enrichment.updated_by = user_id
            db.add(enrichment)
        db.commit()
    except Exception as e:
        db = Session(engine)
        db.exec(
            update(Enrichment)
            .where(Enrichment.id == enrichment.id)
            .values(status=EnrichmentStatus.FAILED)
        )
        db.commit()
        raise e


def matching_company(
    batch: List[Dict[int, EnrichmentItem]],
    mapping_company_list: Dict[str, Dict[str, List[Tuple[int, str]]]],
    column_json_mapping: Dict[int, str],
    mapping_id_to_service_col: Dict[str, str],
    db: Session,
):
    identified_item_ids = []
    entity_map = {}
    failed_item_ids = []
    new_batch = []
    for item in batch:
        try:
            item_row = item[0]
            item_values = {
                mapping_id_to_service_col.get(mapping_id): item[f"label_{mapping_id}"]
                for mapping_id in column_json_mapping.keys()
            }
            # Ưu tiên theo thứ tự: corporate_number > domain > name
            corp_number = item_values.get("corporate_number")
            domain = item_values.get("domain")
            # name = normalize_company_name(item_values.get("name"))
            name = item_values.get("name")

            corp_number_companies = mapping_company_list["corporate_number"].get(
                corp_number, []
            )
            domain_companies = mapping_company_list["domain"].get(domain, [])
            name_companies = mapping_company_list["name"].get(name, [])

            # Logic matching theo thứ tự ưu tiên: corporate_number > domain > name
            matched_company = None

            # Bước 1: Kiểm tra corporate_number (ưu tiên cao nhất)
            if corp_number and len(corp_number_companies) == 1:
                matched_company = corp_number_companies[0]
                print(f"✅ Matched by corporate_number: {matched_company[1]}")
            elif corp_number and len(corp_number_companies) > 1:
                # Có nhiều công ty cùng corp_number, filter theo domain
                if domain:
                    filtered_by_domain = [
                        (cid, cnum)
                        for cid, cnum in corp_number_companies
                        if any(cid == did for did, _ in domain_companies)
                    ]
                    if len(filtered_by_domain) == 1:
                        matched_company = filtered_by_domain[0]
                        print(
                            f"✅ Matched by corporate_number + domain: {matched_company[1]}"
                        )
                    elif len(filtered_by_domain) > 1 and name:
                        # Vẫn nhiều, filter tiếp theo name
                        filtered_by_name = [
                            (cid, cnum)
                            for cid, cnum in filtered_by_domain
                            if any(cid == nid for nid, _ in name_companies)
                        ]
                        if len(filtered_by_name) == 1:
                            matched_company = filtered_by_name[0]
                            print(
                                f"✅ Matched by corporate_number + domain + name: {matched_company[1]}"
                            )
                        elif len(filtered_by_name) > 1:
                            # Thử filter theo normalized_name
                            normalized_name = normalize_company_name(name)
                            if normalized_name:
                                normalized_name_companies = mapping_company_list[
                                    "normalized_name"
                                ].get(normalized_name, [])
                                filtered_by_normalized = [
                                    (cid, cnum)
                                    for cid, cnum in filtered_by_name
                                    if any(
                                        cid == nid
                                        for nid, _ in normalized_name_companies
                                    )
                                ]
                                if len(filtered_by_normalized) == 1:
                                    matched_company = filtered_by_normalized[0]
                                    print(
                                        f"✅ Matched by corporate_number + domain + name + normalized_name: {matched_company[1]}"
                                    )
                                else:
                                    print(
                                        f"❌ Multiple matches after corporate_number + domain + name + normalized_name: {len(filtered_by_normalized)}"
                                    )
                            else:
                                print(
                                    f"❌ Multiple matches after corporate_number + domain + name: {len(filtered_by_name)}"
                                )
                        else:
                            print(
                                f"❌ Multiple matches after corporate_number + domain + name: {len(filtered_by_name)}"
                            )
                    else:
                        print(
                            f"❌ Multiple matches after corporate_number + domain: {len(filtered_by_domain)}"
                        )
                else:
                    print(
                        f"❌ Multiple corporate_number matches, no domain to filter: {len(corp_number_companies)}"
                    )

            # Bước 2: Nếu chưa match, thử domain
            if not matched_company and domain and len(domain_companies) == 1:
                matched_company = domain_companies[0]
                print(f"✅ Matched by domain: {matched_company[1]}")
            elif not matched_company and domain and len(domain_companies) > 1:
                # Nhiều domain matches, filter theo name
                if name:
                    filtered_by_name = [
                        (cid, cnum)
                        for cid, cnum in domain_companies
                        if any(cid == nid for nid, _ in name_companies)
                    ]
                    if len(filtered_by_name) == 1:
                        matched_company = filtered_by_name[0]
                        print(f"✅ Matched by domain + name: {matched_company[1]}")
                    elif len(filtered_by_name) > 1:
                        # Thử filter theo normalized_name
                        normalized_name = normalize_company_name(name)
                        if normalized_name:
                            normalized_name_companies = mapping_company_list[
                                "normalized_name"
                            ].get(normalized_name, [])
                            filtered_by_normalized = [
                                (cid, cnum)
                                for cid, cnum in filtered_by_name
                                if any(
                                    cid == nid for nid, _ in normalized_name_companies
                                )
                            ]
                            if len(filtered_by_normalized) == 1:
                                matched_company = filtered_by_normalized[0]
                                print(
                                    f"✅ Matched by domain + name + normalized_name: {matched_company[1]}"
                                )
                            else:
                                print(
                                    f"❌ Multiple matches after domain + name + normalized_name: {len(filtered_by_normalized)}"
                                )
                        else:
                            print(
                                f"❌ Multiple matches after domain + name: {len(filtered_by_name)}"
                            )
                    else:
                        print(
                            f"❌ Multiple matches after domain + name: {len(filtered_by_name)}"
                        )
                else:
                    print(
                        f"❌ Multiple domain matches, no name to filter: {len(domain_companies)}"
                    )

            # Bước 3: Nếu chưa match, thử name (ưu tiên thấp nhất)
            if not matched_company and name and len(name_companies) == 1:
                matched_company = name_companies[0]
                print(f"✅ Matched by name: {matched_company[1]}")
            elif not matched_company and name and len(name_companies) > 1:
                # Thử filter theo normalized_name
                normalized_name = normalize_company_name(name)
                if normalized_name:
                    normalized_name_companies = mapping_company_list[
                        "normalized_name"
                    ].get(normalized_name, [])
                    filtered_by_normalized = [
                        (cid, cnum)
                        for cid, cnum in name_companies
                        if any(cid == nid for nid, _ in normalized_name_companies)
                    ]
                    if len(filtered_by_normalized) == 1:
                        matched_company = filtered_by_normalized[0]
                        print(
                            f"✅ Matched by name + normalized_name: {matched_company[1]}"
                        )
                    else:
                        print(
                            f"❌ Multiple matches after name + normalized_name: {len(filtered_by_normalized)}"
                        )
                else:
                    print(f"❌ Multiple name matches: {len(name_companies)}")

            # Bước 4: Nếu chưa match, thử normalized_name (ưu tiên thấp nhất)
            if not matched_company and name:
                normalized_name = normalize_company_name(name)
                if normalized_name:
                    normalized_name_companies = mapping_company_list[
                        "normalized_name"
                    ].get(normalized_name, [])
                    if len(normalized_name_companies) == 1:
                        matched_company = normalized_name_companies[0]
                        print(f"✅ Matched by normalized_name: {matched_company[1]}")
                    elif len(normalized_name_companies) > 1:
                        print(
                            f"❌ Multiple normalized_name matches: {len(normalized_name_companies)}"
                        )
                    else:
                        print(
                            f"❌ No normalized_name match found for: {normalized_name}"
                        )
                else:
                    print(f"❌ Could not normalize name: {name}")

            # Kết quả matching
            if matched_company:
                company_id, matched_corp_number = matched_company
                entity_map[item_row.id] = matched_corp_number
                identified_item_ids.append(item_row.id)
                print(f"🎯 Final match: {matched_corp_number} for item {item_row.id}")
            else:
                print(f"❌ No unique match found for item {item_row.id}")
                new_batch.append(item)
        except OperationalError:
            db.rollback()
            failed_item_ids.append(item_row.id)
            continue
    batch = new_batch
    for item in batch:
        item_row = item[0]
        failed_item_ids.append(item_row.id)
    return identified_item_ids, entity_map, failed_item_ids
