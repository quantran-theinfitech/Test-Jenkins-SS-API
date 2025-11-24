from datetime import datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, func
from sqlmodel import Session, and_, select

from app.models.plan import Plan, PlanServiceCode
from app.models.subcription import Subcription
from app.models.team import Team
from app.models.team_credit import PlanCode, ReasonCode, ServiceCode, TeamCredit
from app.models.sequence.mailbox import SequenceMailbox

def create_credit_service(db: Session):
    # Get the current date and time
    now = datetime.now()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    plans = db.exec(
        select(Plan).where(Plan.service_code == PlanServiceCode.LISTING)
    ).all()
    plan_mapping = {plan.name_code: plan for plan in plans}

    expired_today_subscriptions = db.exec(
        select(Subcription, Team)
        .join(Team, Subcription.team_id == Team.id)
        .where(
            Subcription.expire_at <= end_of_day,
            Subcription.is_active,
            Subcription.plan_code != PlanCode.FRE,
        )
    ).all()
    if expired_today_subscriptions:
        subcription_team_ids = set()
        for subscription, team in expired_today_subscriptions:
            if team.id in subcription_team_ids:
                continue
            #unlink all linked mailboxes of this team
            subcription_team_ids.add(team.id)
            team_credit_mailbox_connect = db.exec(
                select(TeamCredit)
                .where(TeamCredit.team_id == team.id)
                .where(TeamCredit.service_code == ServiceCode.MAILBOX_CONNECT)
                .where(TeamCredit.plan_code == subscription.plan_code)
                .where(TeamCredit.is_active)
            ).all()
            for team_credit in team_credit_mailbox_connect:
                team_credit.is_active = False
                linked_mailboxes = db.exec(
                    select(SequenceMailbox)
                    .where(SequenceMailbox.team_id == team.id)
                    .where(SequenceMailbox.deleted_at.is_(None))
                    .limit(team_credit.used_amount)
                ).all()
                for linked_mailbox in linked_mailboxes:
                    linked_mailbox.deleted_at = datetime.now()
                    db.add(linked_mailbox)
                db.add(team_credit)
            subscription.plan_code = PlanCode.FRE
            team.listing_plan_code = PlanCode.FRE
            team.form_plan_code = PlanCode.FRE
    # Get all credits that are active and expired today, get expire_at of subscription
    expired_today_credits = db.exec(
        select(TeamCredit)
        .where(TeamCredit.end_at <= end_of_day)
        .where(TeamCredit.is_active)
        .where(
            TeamCredit.team_id.in_(
                select(Subcription.team_id)
                .where(
                    or_(
                        and_(
                            Subcription.plan_code != PlanCode.FRE,
                            Subcription.expire_at > end_of_day,
                        ),
                        and_(
                            Subcription.plan_code == PlanCode.FRE,
                        ),
                    )
                )
                .where(Subcription.is_active)
            )
        )
    ).all()

    team_ids = {credit.team_id for credit in expired_today_credits}
    subscriptions = db.exec(
        select(Subcription).where(
            Subcription.team_id.in_(team_ids),
            Subcription.is_active,
        )
    ).all()

    subscription_mapping = {sub.team_id: sub for sub in subscriptions}

    # Add rollover credits for all credits that are expired today
    for credit in expired_today_credits:
        start_at = credit.end_at.replace(hour=0, minute=0, second=0, microsecond=0)
        end_at = credit.end_at + relativedelta(months=1)

        # expire all credits
        credit.is_active = False

        # if customize is expire it will not be extended
        if credit.plan_code == PlanCode.CUSTOMIZE:
            continue

        if not subscription_mapping.get(credit.team_id):
            continue

        # get latest plan_code based on subcription table not credit.plan_code
        plan_code = subscription_mapping[credit.team_id].plan_code

        if credit.amount - (credit.used_amount or 0) > 0 and plan_code != PlanCode.FRE:
            # create new credit for next 30 days with reason_code ROLLOVER
            rollover_credit = TeamCredit(
                team_id=credit.team_id,
                service_code=credit.service_code,
                plan_code=plan_code,
                reason_code=ReasonCode.ROLLOVER,
                amount=credit.amount - (credit.used_amount or 0),
                used_amount=0,
                start_at=start_at,
                end_at=end_at,
                is_active=True,
            )
            db.add(rollover_credit)
        # Insert monthly record for all service based on subcription
        start_at = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now.month + 1 > 12:
            end_at = now.replace(year=now.year + 1, month=1, day=now.day)
        else:
            end_at = now.replace(month=now.month + 1, day=now.day)
        plan_code = subscription_mapping[credit.team_id].plan_code
        plan = plan_mapping[plan_code]
        team_id = credit.team_id
        service_code = credit.service_code
        service_quota_mapping = {
            ServiceCode.CPN: "unlock_cpn_quota",
            ServiceCode.PERSON: "unlock_person_quota",
            ServiceCode.EMAIL: "send_email_quota",
            ServiceCode.CSV: "download_csv_quota",
            ServiceCode.TELESALE: "telesale_quota",
            ServiceCode.CTF: "send_form_quota",
            ServiceCode.LINKEDIN_CONNECT: "linkedin_connect_quota",
            ServiceCode.LINKEDIN_MSG: "linkedin_msg_quota",
            ServiceCode.MAILBOX_CONNECT: "mailbox_connect_quota",
        }
        plan_quota = service_quota_mapping[service_code]
        amount = getattr(plan, plan_quota, 0)
        if not amount:
            continue
        db.add(
            TeamCredit(
                team_id=team_id,
                service_code=service_code,
                plan_code=plan_code,
                reason_code=ReasonCode.MONTHLY,
                amount=amount,
                used_amount=0,
                start_at=start_at,
                end_at=end_at,
                is_active=True,
            )
        )
    db.commit()
