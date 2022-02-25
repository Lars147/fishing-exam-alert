from datetime import datetime

import pandas as pd
from pytz import timezone


def localize_datetime(dt: datetime) -> datetime:
    local_tz = timezone("Europe/Berlin")
    return local_tz.localize(dt)


def transform_db_dataframe_for_mail(df: pd.DataFrame) -> pd.DataFrame:
    german_mapping = {
        "exam_id": "Prüfungs-Nr",
        "name": "Prüfungslokal",
        "street": "Straße",
        "street_number": "Haus-Nr.",
        "city": "Ort",
        "postal_code": "PLZ",
        "district": "Regierungsbezirk",
        "exam_start": "Prüfungsbeginn",
        "min_participants": "Min. Teilnehmer",
        "max_participants": "Max. Teilnehmer",
        "current_participants": "Aktuelle Teilnehmer",
        "status": "Status",
        "disabled_access": "Behindertengerecht",
        "headphones": "Kopfhörer",
    }
    renamed_df = df.rename(columns=german_mapping)
    return renamed_df.drop(["id", "created_at", "updated_at"], axis=1)
