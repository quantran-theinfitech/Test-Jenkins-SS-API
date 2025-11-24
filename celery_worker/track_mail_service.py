from datetime import timedelta

from sqlmodel import Session

# from app.models.sequence.campaign import SequenceCampaign
from external.mail_tracking import MailTrackingService

different_time_since_last_check = timedelta(hours=2)
maximum_check_interval = timedelta(weeks=2)


def track_bounced_mail_service(
    db: Session,
    last_check_time_in_minute: int,
    maximum_interval_in_days: int,
):
    different_time_since_last_check = timedelta(minutes=last_check_time_in_minute)
    maximum_check_interval = timedelta(days=maximum_interval_in_days)
    service = MailTrackingService()
    # campaign_ids = db.exec(
    #     select(SequenceCampaign.id).where(SequenceCampaign.deleted_at.is_(None))
    # ).all()
    # if not campaign_ids:
    #     print("No campaign found")
    # else:
    #     for campaign_id in campaign_ids:
    print("Checking bounced mail in all sequences")
    bounced_id = service.bounced_tracking(
        different_time_since_last_check, db, maximum_check_interval
    )
    print(f"Bounced ID: {bounced_id}")
    return bounced_id


def track_replied_mail_service(
    db: Session,
    maximum_interval_in_days: int,
):
    maximum_check_interval = timedelta(days=maximum_interval_in_days)
    service = MailTrackingService()
    # campaign_ids = db.exec(
    #     select(SequenceCampaign.id).where(SequenceCampaign.deleted_at.is_(None))
    # ).all()
    # if not campaign_ids:
    #     print("No campaign found")
    # else:
    # for campaign_id in campaign_ids:
    print("Checking replied mail in all sequences")
    replied_id = service.replied_tracking(db, maximum_check_interval)
    print(f"Replied ID: {replied_id}")
    return replied_id
