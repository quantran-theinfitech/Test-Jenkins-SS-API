# flake8: noqa
from datetime import datetime

from sqlalchemy.sql import text
from sqlmodel import Session, select

from app.models.team import PlanCode
from app.models.team_credit import ReasonCode, ServiceCode, TeamCredit


def get_priority(credit):
    """
    1. reason_code='ROLLOVER', plan_code != 'CUSTUMIZE'
    2. reason_code!='ROLLOVER', plan_code != 'CUSTUMIZE'
    3. reason_code='ROLLOVER', plan_code = 'CUSTUMIZE'
    4. reason_code!='ROLLOVER', plan_code = 'CUSTUMIZE'
    """
    if (
        credit.reason_code == ReasonCode.ROLLOVER
        and credit.plan_code != PlanCode.CUSTOMIZE
    ):
        return 1
    elif (
        credit.reason_code != ReasonCode.ROLLOVER
        and credit.plan_code != PlanCode.CUSTOMIZE
    ):
        return 2
    elif (
        credit.reason_code == ReasonCode.ROLLOVER
        and credit.plan_code == PlanCode.CUSTOMIZE
    ):
        return 3
    else:
        return 4


def consume_credit(db: Session, team_id: int, amount: int, service_code: ServiceCode):
    now = datetime.now()
    available_credits = db.exec(
        select(TeamCredit)
        .where(TeamCredit.team_id == team_id)
        .where(TeamCredit.start_at <= now)
        .where(TeamCredit.end_at >= now)
        .where(TeamCredit.is_active)
        .where(TeamCredit.service_code == service_code)
        .where(TeamCredit.amount > TeamCredit.used_amount)
    ).all()
    sorted_credits = sorted(
        available_credits,
        key=get_priority,
    )

    remaining_credits = amount

    for credit in sorted_credits:
        if remaining_credits <= 0:
            break

        available_credit = credit.amount - credit.used_amount
        if available_credit <= 0:
            continue

        credit_to_use = min(available_credit, remaining_credits)
        credit.used_amount += credit_to_use
        credit.updated_at = datetime.now()

        remaining_credits -= credit_to_use
    db.commit()


def consume_credit_with_atomic_update(
    db: Session, team_id: int, amount: int, service_code: ServiceCode
):
    if amount <= 0:
        return

    now = datetime.now()
    available_credits = db.exec(
        select(TeamCredit)
        .where(TeamCredit.team_id == team_id)
        .where(TeamCredit.start_at <= now)
        .where(TeamCredit.end_at >= now)
        .where(TeamCredit.is_active)
        .where(TeamCredit.service_code == service_code)
        .where(TeamCredit.amount > TeamCredit.used_amount)
        # .with_for_update()
    ).all()
    sorted_credits = sorted(
        available_credits,
        key=get_priority,
    )

    consume_query = text(
        """
        UPDATE team_credits
        SET used_amount = used_amount + :inc,
            updated_at = now()
        WHERE id = :id
          AND used_amount + :inc <= amount
        RETURNING id
        """
    )

    remaining_credits = amount
    consumed = 0

    for credit in sorted_credits:
        if remaining_credits <= 0:
            break

        available_credit = credit.amount - credit.used_amount
        if available_credit <= 0:
            continue

        inc = (
            remaining_credits
            if remaining_credits <= available_credit
            else available_credit
        )
        if inc <= 0:
            continue

        updated = db.execute(consume_query, {"inc": inc, "id": credit.id}).first()
        if not updated:
            print(f"Credit {credit.id} skipped due to insufficient balance")
            continue

        remaining_credits -= inc
        consumed += inc

    if consumed > 0:
        db.commit()

    return consumed == amount


def get_credit_status(db: Session, team_id: int):
    credit_query = f"""
            SELECT SUM(amount) as amount,
                   SUM(used_amount) as used_amount,
                   service_code
            FROM team_credits
            WHERE team_id=:team_id
                AND start_at <= now()
                AND end_at >= now()
                AND is_active = true
            GROUP BY service_code
            ORDER BY CASE service_code
                WHEN '{ServiceCode.CSV}' THEN 1
                WHEN '{ServiceCode.EMAIL}' THEN 2
                WHEN '{ServiceCode.CPN}' THEN 3
                WHEN '{ServiceCode.PERSON}' THEN 4
                WHEN '{ServiceCode.CTF}' THEN 5
                WHEN '{ServiceCode.LINKEDIN_CONNECT}' THEN 6
                WHEN '{ServiceCode.LINKEDIN_MSG}' THEN 7
                WHEN '{ServiceCode.MAILBOX_CONNECT}' THEN 8
                ELSE 9
            END
        """
    return db.execute(text(credit_query), {"team_id": team_id}).all()


def is_enough_credit(
    db: Session,
    team_id: int,
    amount_will_spend: int,
    service_code: ServiceCode = ServiceCode.CPN,
) -> bool:
    try:
        amount_query = """
                SELECT SUM(amount) as amount,
                    SUM(used_amount) as used_amount
                FROM team_credits
                WHERE service_code= :service_code_name
                    AND team_id=:team_id
                    AND start_at <= now()
                    AND end_at >= now()
                    AND is_active = true
                    AND deleted_at IS NULL
                    AND amount > used_amount
                GROUP BY team_id
            """
        amount, used_amount = db.execute(
            text(amount_query),
            {"service_code_name": service_code.name, "team_id": team_id},
        ).one() or (0, 0)
    except Exception:
        return False
    return amount >= used_amount + amount_will_spend
