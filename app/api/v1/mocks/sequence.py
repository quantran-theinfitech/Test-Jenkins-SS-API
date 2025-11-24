from random import randint, choice
from app.api.v1.schemas.sequence.campaigns import SequenceBase, SequenceDetailResponse


def generate_mock_sequence(id: int) -> SequenceBase:
    return SequenceBase(
        id=id,
        created_by=randint(1, 100),
        name=f"Sequence {id}",
        is_active=choice([True, False]),
        active_count=randint(0, 100),
        paused_count=randint(0, 50),
        not_sent_count=randint(0, 10),
        bounced_count=randint(0, 10),
        spam_blocked_count=randint(0, 5),
        finished_count=randint(0, 30),
        scheduled_count=randint(0, 100),
        delivered_count=randint(0, 100),
        reply_count=randint(0, 50),
        interested_count=randint(0, 30),
    )


def generate_mock_listing_sequence(page: int, per_page: int) -> dict:
    total = 50
    data = [
        generate_mock_sequence(id)
        for id in range((page - 1) * per_page + 1, page * per_page + 1)
    ]
    return {"page": page, "per_page": per_page, "total": total, "data": data}


def generate_mock_sequence_detail(sequence_id: int) -> SequenceDetailResponse:
    return SequenceDetailResponse(
        id=sequence_id,
        created_by=randint(1, 100),
        name=f"Sequence {sequence_id}",
        is_active=choice([True, False]),
        active_count=randint(0, 100),
        paused_count=randint(0, 50),
        not_sent_count=randint(0, 10),
        bounced_count=randint(0, 10),
        spam_blocked_count=randint(0, 5),
        finished_count=randint(0, 30),
        scheduled_count=randint(0, 100),
        delivered_count=randint(0, 100),
        reply_count=randint(0, 50),
        interested_count=randint(0, 30),
        schedule_id=1,
    )
