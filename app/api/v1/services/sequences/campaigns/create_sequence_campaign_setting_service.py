from sqlmodel import Session

from app.models.sequence.campaign_setting import SequenceCampaignSetting


def create_sequence_campaign_default_setting_service(
    campaign_id: int,
    db: Session,
):
    try:
        setting = SequenceCampaignSetting(
            sequence_campaign_id=campaign_id,
            days_until_unresponsive=5,
            stage_list_as_not_sent=[],
            is_finished_when_replied=True,
            is_finished_when_unsubscribed=True,
            is_status_change_when_bounced=True,
            cc_list=[],
            bcc_list=[],
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
        return setting
    except Exception as e:
        db.rollback()
        raise e
