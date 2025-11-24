import json
import random
import string
from datetime import datetime, timedelta, timezone

import gspread
from google.oauth2.service_account import Credentials
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.config import settings
from app.models.group import Group
from app.models.plan import PlanServiceCode
from app.models.subcription import Subcription
from app.models.team import PlanCode, Team
from app.models.team_credit import ReasonCode, TeamCredit
from app.models.user import RoleCode, Source, TeamMemberRoleCode, User

MAPPING = {
    "company_name": "会社名",
    "email": "メールアドレス",
    "tel": "電話番号",
    "position_code": "役職",
    "department_name": "部署",
    # "お問い合わせ内容": "",
    # "ご質問・ご要望": "",
}

MULTIPLE_MAPPING = {
    "name": ["姓", "名"],
}

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.SECURITY_BCRYPT_DEFAULT_ROUNDS,
)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def generate_password(length=12, use_symbols=True):
    characters = string.ascii_letters + string.digits
    if use_symbols:
        characters += string.punctuation

    password = "".join(random.choice(characters) for _ in range(length))
    return password


def get_all_records_as_strings(sheet, empty2zero=False, head=1):
    """Recreate `get_all_records()` but force everything to stay as strings."""
    data = sheet.get_all_values()
    headers = data[head - 1]
    records = []

    for row in data[head:]:
        # Extend the row if it's shorter than headers
        row += [""] * (len(headers) - len(row))

        record = {}
        for key, value in zip(headers, row):
            if value == "" and empty2zero:
                value = "0"
            record[key] = value
        records.append(record)

    return records


async def upsert_user_from_hubspot_google_sheet(db: Session):
    # Define the scope
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # Authenticate
    credentials = Credentials.from_service_account_info(
        json.loads(settings.HUBSPOT_GOOGLE_SERVICE_ACCOUNT),
        scopes=SCOPES,
    )

    # Connect to Google Sheets
    gc = gspread.authorize(credentials)

    spreadsheet = gc.open_by_url(settings.HUBSPOT_GOOGLE_SHEET_URL)

    # Select the first worksheet
    worksheet = spreadsheet.sheet1

    # Get all values
    data = get_all_records_as_strings(worksheet)

    index = 1
    insert_values = []
    new_users = {}
    for row in data:
        index += 1
        email = row.get(MAPPING["email"])
        values = ["", ""]
        if not email:
            print("no email")
            insert_values.append(values)
            continue
        if new_users.get(email):
            insert_values.append([new_users.get(email).get("id"), ""])
            continue
        user = db.exec(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        ).first()
        is_generated_password = False
        is_new_user = False
        password = None
        if not user:
            is_new_user = True
            is_generated_password = True
            password = generate_password()
            user = User(
                email=email,
                initial_password=get_password_hash(password),
                role_code=RoleCode.User,
                source=Source.ANDIGITAL_FORM,
                team_member_role_code=TeamMemberRoleCode.MANAGER,
            )
            new_team = Team(listing_plan_code=PlanCode.FRE, form_plan_code=PlanCode.FRE)
            db.add(new_team)
            db.flush()
            db.refresh(new_team)
            user.team_id = new_team.id
            now = datetime.now(timezone.utc)
            start_of_next_month = (now.replace(day=1) + timedelta(days=32)).replace(
                day=1
            )
            new_listing_subscription = Subcription(
                team_id=new_team.id,
                plan_code=new_team.listing_plan_code,
                service_code=PlanServiceCode.LISTING,
                expire_at=(
                    start_of_next_month
                    if new_team.listing_plan_code != PlanCode.FRE
                    else None
                ),
                start_at=now,
            )
            new_form_subscription = Subcription(
                team_id=new_team.id,
                plan_code=new_team.form_plan_code,
                service_code=PlanServiceCode.FORM,
                expire_at=(
                    start_of_next_month
                    if new_team.form_plan_code != PlanCode.FRE
                    else None
                ),
                start_at=now,
            )
            db.add(new_listing_subscription)
            db.add(new_form_subscription)

            new_company_credit = TeamCredit(
                team_id=new_team.id,
                service_code=PlanServiceCode.CPN,
                plan_code=PlanCode.FRE,
                reason_code=ReasonCode.MONTHLY,
                amount=500,
                used_amount=0,
                start_at=now,
                end_at=start_of_next_month,
                is_active=True,
            )

            new_person_credit = TeamCredit(
                team_id=new_team.id,
                service_code=PlanServiceCode.PERSON,
                plan_code=PlanCode.FRE,
                reason_code=ReasonCode.MONTHLY,
                amount=20,
                used_amount=0,
                start_at=now,
                end_at=start_of_next_month,
                is_active=True,
            )

            db.add(new_company_credit)
            db.add(new_person_credit)

            new_group = Group(
                team_id=new_team.id,
                name="デフォルト",
                description="自動生成のグループ",
                default_flag=1,
            )
            db.add(new_group)

        for key, header in MAPPING.items():
            if row.get(header):
                setattr(user, key, row.get(header))
        for key, headers in MULTIPLE_MAPPING.items():
            value = ""
            for header in headers:
                value += f"{row.get(header)} "
            if value != "":
                setattr(user, key, value)
        db.add(user)
        db.flush()
        db.refresh(user)
        if is_new_user:
            new_users[user.email] = {
                "id": user.id,
                "email": user.email,
                "password": password,
            }
        values = [user.id]
        if is_generated_password:
            values.append(password)
        insert_values.append(values)

    try:
        db.commit()
        # Không cần gửi mail nữa
        # for data in list(new_users.values()):
        #     message = MessageSchema(
        #         subject="【SalesSmart】のメンバーとして登録しました",
        #         recipients=[EmailStr(data.get("email"))],
        #         template_body=data,
        #         subtype=MessageType.html,
        #     )
        #     fm = FastMail(mail_connection())

        #     await fm.send_message(message, template_name="register_from_hubspot.html")
        worksheet.update(insert_values, f"L2:M{index}")
    except Exception as e:
        print(e)
        return
