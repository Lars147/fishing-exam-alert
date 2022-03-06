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


def create_random_exam(db: Session) -> models.Exam:
    exam_defaults = get_random_valid_exam_addresses()
    exam_defaults["name"] = "Test Exam"
    exam_defaults["status"] = "Frei"
    exam_defaults["exam_start"] = datetime.now() + timedelta(weeks=1)
    exam_defaults["min_participants"] = 1
    exam_defaults["max_participants"] = 10
    exam_defaults["current_participants"] = 7
    exam_defaults["disabled_access"] = True
    exam_defaults["headphones"] = True

    exam, _ = models.Exam.get_or_create(db=db, exam_id="0001", defaults=exam_defaults)

    return exam


def get_random_valid_exam_addresses() -> Dict[str, Any]:
    return {
        "street": "Herzogspitalstraße",
        "street_number": "24",
        "city": "München",
        "postal_code": "80331",
        "district": models.District.Oberbayern,
    }
