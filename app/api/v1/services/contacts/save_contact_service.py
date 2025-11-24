from fastapi import UploadFile
from pandas import DataFrame, notnull, read_csv
from sqlalchemy import null, text
from sqlmodel import Session

from app.api.base.exceptions import BadRequestException
from app.api.v1.schemas.engagements import ContactListFieldName, SaveContactRequest
from app.api.v1.schemas.users import UserBase
from app.models import Contact


def save_contact(
    request: SaveContactRequest,
    db: Session,
    current_user: UserBase,
):
    contact = request.data
    corporate_number = []
    uuid = null
    search_person_query = """SELECT *
            FROM persons p
            WHERE p.email = :email
            """
    person = db.execute(
        text(search_person_query),
        {
            "email": contact.email,
        },
    ).all()

    # if there is only one person match the condition
    if len(person) == 1:
        uuid = person[0].uuid
        corporate_number = person[0].corporate_number
    # there is no person match the condition
    else:
        search_company_query = """SELECT corporate_number
            FROM companies c
            WHERE c.name = :name
            """
        corp_number = db.execute(
            text(search_company_query),
            {"name": contact.company_name, "team_id": current_user.team_id},
        ).one_or_none()

        # if the company is exist
        if corp_number:
            corporate_number = list(corp_number)

    data = Contact(
        id=contact.id,
        team_id=current_user.id,
        corporate_number=corporate_number,
        person_uuid=uuid,
        name=contact.name,
        bio=contact.bio,
        email=contact.email,
        address=contact.address,
        skills=contact.skills,
        company_name=contact.company_name,
        status_code=contact.status_code,
        linkedin_url=contact.linkedin_url,
        twitter_url=contact.twitter_url,
        github_url=contact.github_url,
        note_url=contact.note_url,
        fb_url=contact.fb_url,
        contact_times=contact.contact_times,
        inbox_times=contact.inbox_times,
        potential_action=contact.potential_action_at,
        site_usage=contact.site_usage_at,
        change_history=contact.change_history_at,
        lead_source_code=contact.lead_source_code,
        tags=contact.tags,
    )
    db.add(data)
    db.flush()
    db.commit()
    return data.id


def read_contact_list_csv(file: UploadFile):
    if file.content_type != "text/csv":
        raise BadRequestException(detail="uploadfile.incorrectFormat")
    else:
        fieldnames = [fieldname.value for fieldname in ContactListFieldName]
        df = read_csv(file.file, keep_default_na=False)
        df = df.astype(str)
        df = df.replace("", None)

        for fieldname in df.columns.to_list():
            if fieldname not in fieldnames:
                raise BadRequestException(detail="uploadfile.incorrectFormat")
        if not notnull(df["email"]).all():
            raise BadRequestException(detail="uploadfile.incorrectFormat")
        file.file.close()
        return df


def save_contacts_from_csv(db: Session, current_user: UserBase, df: DataFrame):
    try:
        data_list = []
        for i in range(len(df)):
            corporate_number = []
            uuid = null
            search_person_query = """SELECT *
                FROM persons p
                WHERE p.email = :email
                """
            person = db.execute(
                text(search_person_query),
                {
                    "email": df.at[i, "email"],
                },
            ).all()

            # if there is only one person match the condition
            if len(person) == 1:
                uuid = person[0].uuid
                corporate_number = person[0].corporate_number
            # there is no person match the condition
            else:
                search_company_query = """SELECT corporate_number
                FROM companies c
                WHERE c.name = :name
                """
                corp_number = db.execute(
                    text(search_company_query),
                    {"name": df.at[i, "company_name"], "team_id": current_user.team_id},
                ).one_or_none()

                # if the company is exist
                if corp_number:
                    corporate_number = list(corp_number)

            data = Contact(
                team_id=current_user.id,
                corporate_number=corporate_number,
                person_uuid=uuid,
                name=df.at[i, "name"],
                bio=df.at[i, "bio"],
                email=df.at[i, "email"],
                address=df.at[i, "address"],
                skills=df.at[i, "skills"],
                company_name=df.at[i, "company_name"],
                status_code=df.at[i, "status_code"],
                linkedin_url=df.at[i, "linkedin_url"],
                twitter_url=df.at[i, "twitter_url"],
                github_url=df.at[i, "github_url"],
                note_url=df.at[i, "note_url"],
                fb_url=df.at[i, "fb_url"],
                contact_times=df.at[i, "contact_times"],
                inbox_times=df.at[i, "inbox_times"],
                potential_action_at=df.at[i, "potential_action_at"],
                site_usage_at=df.at[i, "site_usage_at"],
                change_history_at=df.at[i, "change_history_at"],
                lead_source_code=df.at[i, "lead_source_code"],
                # tags=contact.tags,
            )
            data_list.append(data)

        db.add_all(data_list)
        db.flush()
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return 1
