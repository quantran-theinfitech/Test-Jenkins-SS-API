import uuid
from datetime import datetime
from typing import Dict

import pandas as pd
from sqlalchemy import or_
from sqlmodel import Session, func, or_, select

from app.models.sequence.campaign_contacts import SequenceCampaignContacts
from app.models.sequence.campaign_import import (
    SequenceCampaignImport,
    UploadProcessStatus,
)
from app.models.sequence.campaign_import_item import SequenceCampaignImportItem
from app.models.sequence.contact import (
    ContactType,
    SequenceContact,
    SequencePersonStage,
)
from app.models.sequence.linkedin_account import LinkedInAccount, LinkedInAccountStatus


def save_to_db(
    campaign: Dict,
    df: Dict,
    db: Session,
    import_id: int,
    total: int,
    team_id: int,
):
    sequence_campaign_id = campaign["id"]
    df = pd.DataFrame(df)
    new_persons = []
    persons = []
    err_message = None
    field_mapping = {
        "fb_url": "フェイスブックのURL",
        "wantedly_url": "ワンテドリーのURL",
        "linkedin_url": "リンクインのURL",
        "github_url": "ギットハブのURL",
        "twitter_url": "ツイッターのURL",
        "note_url": "ノートのURL",
        "address": "住所",
        "intro": "自己紹介",
        "bio": "情報",
        "corporate_number": "法人番号",
        "role_name": "役職",
        "company_name": "企業名",
        "role_group_codes": "役職グループ",
    }
    list_type_field = ["役職グループ", "企業名", "役職", "法人番号"]

    account_linkedin = (
        db.query(LinkedInAccount)
        .filter(
            LinkedInAccount.team_id == team_id,
            LinkedInAccount.deleted_at.is_(None),
            LinkedInAccount.is_default.is_(True),
        )
        .first()
    )

    if "氏名" in df.columns and "メール" in df.columns and "リンクインのURL" in df.columns:
        try:
            email_list = []
            linkedin_list = []
            for index, data in df.iterrows():
                # if data["氏名"] is None or data["メール"] is None:
                #     err_message = "sequence.missingNameOrEmail"
                #     return err_message
                email_list.append(data["メール"])
                linkedin_list.append(data["リンクインのURL"])
            condition = [
                or_(
                    SequenceContact.email.in_(email_list),
                    SequenceContact.linkedin_url.in_(linkedin_list),
                ),
                SequenceContact.sequence_campaign_id == sequence_campaign_id,
                SequenceContact.deleted_at.is_(None),
            ]
            query = select(SequenceContact).where(*condition)
            response = db.exec(query).all()
            import_items = []
            existed_contact_email_dict = {
                contact.email: contact for contact in response
            }
            existed_contact_linkedin_dict = {
                contact.linkedin_url: contact for contact in response
            }
            for index, data in df.iterrows():
                if data["メール"] in existed_contact_email_dict:
                    person = existed_contact_email_dict[data["メール"]]
                    # person.name = str(data["氏名"])
                    # for key, value in field_mapping.items():
                    #     if value in df.columns:
                    #         if value in list_type_field:
                    #             data_list = str(data[value]).split(",")
                    #             setattr(person, key, data_list)
                    #         else:
                    #             setattr(person, key, data[value])
                    persons.append(person)
                    continue
                elif data["リンクインのURL"] in existed_contact_linkedin_dict:
                    person = existed_contact_linkedin_dict[data["リンクインのURL"]]
                    persons.append(person)
                    continue
                else:
                    user_uuid = uuid.uuid4()
                    # while db.exec(
                    #     select(SequenceContact).where(
                    #         SequenceContact.uuid == str(user_uuid)
                    #     )
                    # ).first():
                    #     user_uuid = uuid.uuid4()
                    sequence_person = SequenceContact(
                        sequence_campaign_id=sequence_campaign_id,
                        uuid=str(user_uuid),
                        name=str(data["氏名"]),
                        email=data["メール"] if pd.notna(data["メール"]) else None,
                        current_step=1,
                        stage=SequencePersonStage.COLD,
                        target_type=ContactType.PERSON,
                    )
                    for key, value in field_mapping.items():
                        if value in df.columns:
                            if value in list_type_field:
                                data_list = str(data[value]).split(",")
                                setattr(sequence_person, key, data_list)
                            else:
                                field_value = (
                                    data[value] if pd.notna(data[value]) else None
                                )
                                setattr(sequence_person, key, field_value)
                    new_persons.append(sequence_person)
            db.add_all(new_persons)
            db.flush()

            for sequence_person in new_persons:
                import_item = SequenceCampaignImportItem(
                    sequence_campaign_import_id=import_id,
                    sequence_person_id=sequence_person.id,
                )
                import_items.append(import_item)
            for person in persons:
                import_item = SequenceCampaignImportItem(
                    sequence_campaign_import_id=import_id,
                    sequence_person_id=person.id,
                )
                import_items.append(import_item)
            db.add_all(import_items)
        except (SyntaxError, TypeError):
            err_message = "sequence.invalidDataType"
            return err_message
        db.flush()
        campaign_persons = []
        for person in new_persons:
            person_status = (
                "PAUSE"
                if account_linkedin
                and account_linkedin.status == LinkedInAccountStatus.CREDENTIALS.value
                else ("ACTIVE" if campaign["is_active"] else "PAUSE")
            )

            campaign_persons.append(
                SequenceCampaignContacts(
                    sequence_campaign_id=sequence_campaign_id,
                    sequence_contact_id=person.id,
                    status=person_status,
                    time_resumed=datetime.now() if person_status == "ACTIVE" else None,
                )
            )

        db.add_all(campaign_persons)
        db.commit()
        query = (
            select(SequenceCampaignImport)
            .where(SequenceCampaignImport.id == import_id)
            .with_for_update()
        )
        import_file = db.exec(query).first()
        if import_file.upload_process_status != UploadProcessStatus.FINISHED.value:
            query = select(func.count(SequenceCampaignImportItem.id)).where(
                SequenceCampaignImportItem.sequence_campaign_import_id == import_id
            )
            item_count = db.exec(query).first()
            if item_count == total:
                import_file.upload_process_status = UploadProcessStatus.FINISHED.value
        db.commit()
        return err_message
    else:
        err_message = "sequence.missingNameOrEmail"
        return err_message
