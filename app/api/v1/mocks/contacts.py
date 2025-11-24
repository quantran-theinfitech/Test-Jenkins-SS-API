from datetime import datetime
from random import randint, choice
from app.api.v1.schemas.sequence.persons import (
    SequencePersonsBase,
    ListingSequencePersonsResponse,
    SequencePersonDetailResponse,
    SequenceStatus
)


def generate_mock_contact(id: int) -> SequencePersonsBase:
    return SequencePersonsBase(
        id=id,
        name=f"User {id}",
        email=f"user{id}@example.com",
        linkedin_url=f"https://linkedin.com/in/user{id}",
        twitter_url=f"https://twitter.com/user{id}",
        hubspot_id=str(randint(1000, 9999)),
        phone=f"+1 234-567-{randint(100, 999)}",
        status=choice(["active", "inactive", "pending", "blocked"]),
        current_step=randint(1, 10),
        company_id=randint(1, 100),
    )


def generate_mock_listing_contact(
    page: int, per_page: int
) -> ListingSequencePersonsResponse:
    total = 20
    data = [
        generate_mock_contact(id)
        for id in range((page - 1) * per_page + 1, page * per_page + 1)
    ]

    return ListingSequencePersonsResponse(
        page=page, per_page=per_page, total=total, data=data
    )


def generate_mock_contact_detail(
    sequence_id: int, contact_id: int
) -> SequencePersonDetailResponse:
    return SequencePersonDetailResponse(
        id=contact_id,
        name="Christian Luedders",
        email="christian.luedders@example.com",
        linkedin_url="https://www.linkedin.com/in/christianluedders",
        twitter_url="https://twitter.com/christianluedders",
        hubspot_id="HS123456",
        phone="+1234567890",
        status="Active",
        current_step=2,
        company_id=101,
        sequence_name="test new sequence",
        added_on=datetime(2025, 1, 11),
        added_by=123,
        status_history=[
            SequenceStatus(
                action="Added to sequence", action_date=datetime(2025, 1, 11)
            ),
            SequenceStatus(action="Paused", action_date=datetime(2025, 1, 15)),
            SequenceStatus(action="Resumed", action_date=datetime(2025, 1, 21)),
        ],
    )
