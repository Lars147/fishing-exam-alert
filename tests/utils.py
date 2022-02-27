from datetime import datetime, timedelta
from typing import Any, Dict

from sqlmodel import Session

from fishing_exam_alert import models
from fishing_exam_alert.settings import setting


def create_random_user(db: Session) -> models.User:
    defaults = {"active": True, "postal_code": "80335", "max_travel_duration": 60}

    user, _ = models.User.get_or_create(db=db, email=setting.TEST_EMAIL, defaults=defaults)
    return user


def create_random_exam(db: Session) -> models.Exam:
    exam_defaults = get_random_valid_exam_addresses()
    exam_defaults["name"] = "Test Exam"
    exam_defaults["status"] = "Frei"
    exam_defaults["exam_start"] = datetime.utcnow() + timedelta(weeks=1)
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
