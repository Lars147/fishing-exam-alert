import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from faker import Faker
from sqlmodel import Session

from fishing_exam_alert import models


def get_random_email(locale: Optional[str] = None) -> str:
    fake = Faker(locale=locale)
    return fake.email()


def get_random_districts() -> List[models.District]:
    return random.sample(list(models.District), random.randint(1, 6))


def get_random_user(
    id: Optional[int] = None,
    email: Optional[str] = None,
    max_travel_duration: Optional[int] = None,
    postal_code: Optional[str] = None,
    districts: Optional[str] = None,
    need_headphones: Optional[bool] = None,
    need_disabled_access: Optional[bool] = None,
    active: Optional[bool] = None,
    locale: str = "de_DE",
) -> models.User:
    fake = Faker(locale=locale)

    return models.User(
        id=id,
        email=email or get_random_email(locale=locale),
        max_travel_duration=max_travel_duration or fake.random_int(min=0, max=120),
        postal_code=postal_code or fake.postalcode(),
        districts=districts or ",".join(get_random_districts()),
        need_headphones=need_headphones or fake.boolean(),
        need_disabled_access=need_disabled_access or fake.boolean(),
        active=active or fake.boolean(),
        created_at=None,
        updated_at=None,
    )


def create_random_user(
    db: Session,
    email: Optional[str] = None,
    max_travel_duration: int = 120,
    postal_code: str = "80335",
    districts: Optional[str] = None,
    need_headphones: Optional[bool] = None,
    need_disabled_access: Optional[bool] = None,
    active: bool = True,
) -> models.User:

    email = email or get_random_email()

    defaults = {
        "max_travel_duration": max_travel_duration,
        "postal_code": postal_code,
        "districts": districts,
        "need_headphones": need_headphones,
        "need_disabled_access": need_disabled_access,
        "active": active,
    }

    user, _ = models.User.update_or_create(db=db, email=email, defaults=defaults)
    return user


def get_random_exam(
    id: Optional[int] = None,
    exam_id: Optional[str] = None,
    name: Optional[str] = None,
    street: Optional[str] = None,
    street_number: Optional[str] = None,
    city: Optional[str] = None,
    postal_code: Optional[str] = None,
    district: Optional[models.District] = None,
    exam_start: Optional[datetime] = None,
    min_participants: Optional[int] = None,
    max_participants: Optional[int] = None,
    current_participants: Optional[int] = None,
    status: Optional[str] = None,
    disabled_access: Optional[bool] = None,
    headphones: Optional[bool] = None,
    locale: str = "de_DE",
) -> models.Exam:
    fake = Faker(locale=locale)

    min_participants = min_participants or random.randint(1, 40)
    max_participants = max_participants or random.randint(min_participants, min_participants + 100)
    current_participants = current_participants or random.randint(min_participants, max_participants)
    if not status:
        status = "Belegt" if current_participants == max_participants else "Frei"

    return models.Exam(
        id=id,
        exam_id=exam_id or str(random.randint(1, 9999)),
        name=name or fake.name(),
        street=street or fake.street_name(),
        street_number=street_number or fake.building_number(),
        city=city or fake.city(),
        postal_code=postal_code or fake.postalcode(),
        district=district or random.choice(list(models.District)),
        exam_start=exam_start or datetime.now() + timedelta(weeks=1),
        min_participants=min_participants,
        max_participants=max_participants,
        current_participants=current_participants,
        status=status,
        disabled_access=disabled_access or fake.boolean(),
        headphones=headphones or fake.boolean(),
        created_at=None,
        updated_at=None,
    )


def create_random_exam(
    db: Session,
    exam_id: Optional[str] = None,
    name: str = "Test Exam",
    street: str = "Herzogspitalstraße",
    street_number: str = "24",
    city: str = "München",
    postal_code: str = "80331",
    district: models.District = models.District.Oberbayern,
    exam_start: Optional[datetime] = None,
    min_participants: int = 1,
    max_participants: int = 10,
    current_participants: int = 7,
    status: str = "Frei",
    disabled_access: Optional[bool] = None,
    headphones: Optional[bool] = None,
) -> models.Exam:

    exam_in = get_random_exam(
        exam_id=exam_id,
        name=name,
        street=street,
        street_number=street_number,
        city=city,
        postal_code=postal_code,
        district=district,
        exam_start=exam_start,
        min_participants=min_participants,
        max_participants=max_participants,
        current_participants=current_participants,
        status=status,
        disabled_access=disabled_access,
        headphones=headphones,
    )

    defaults = exam_in.dict()

    exam, _ = models.Exam.get_or_create(db=db, exam_id=exam_in.exam_id, defaults=defaults)

    return exam
