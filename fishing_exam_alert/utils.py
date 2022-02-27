from datetime import datetime
from urllib.parse import quote_plus

import googlemaps
import pandas as pd
import requests
from loguru import logger
from pytz import timezone

from fishing_exam_alert.settings import setting


def localize_datetime(dt: datetime) -> datetime:
    local_tz = timezone("Europe/Berlin")
    return local_tz.localize(dt)


def dt_to_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone("UTC"))


def localize_dt_to_utc(dt: datetime) -> datetime:
    dt_localized = localize_datetime(dt)
    return dt_to_utc(dt_localized)


def dt_to_local(dt: datetime) -> datetime:
    return dt.astimezone(timezone("Europe/Berlin"))


def transform_db_dataframe_for_mail(df: pd.DataFrame) -> pd.DataFrame:
    transformed_df = df.copy()
    german_mapping = {
        "exam_id": "Prüfungs-Nr",
        "name": "Prüfungslokal",
        "address_line": "Adresse",
        "district": "Regierungsbezirk",
        "exam_start_german_time": "Prüfungsbeginn",
        "min_participants": "Min. Teilnehmer",
        "participants": "Belegte Plätze",  # calculated row in this func
        "status": "Status",
        "disabled_access": "Behindertengerecht",
        "headphones": "Kopfhörer",
        "address_line": "Adresse",
        "travel_duration_in_min": "Entfernung Fahrzeit [min]",  # calculated row in this func
        "travel_distance_in_km": "Entfernung [km]",  # calculated row in this func
        "directions_url": "Route",  # calculated row in this func
    }
    if "travel_duration" in transformed_df:  # transform duration from second to minute
        transformed_df["travel_duration_in_min"] = transformed_df["travel_duration"].apply(lambda x: int(x / 60))
    if "travel_distance" in transformed_df:  # transform distance from meter to kilometer
        transformed_df["travel_distance_in_km"] = transformed_df["travel_distance"].apply(lambda x: int(x / 1000))

    # combine participant occupancy to one column
    transformed_df["participants"] = transformed_df.apply(
        lambda row: f"{row.current_participants} / {row.max_participants}", axis=1
    )

    # create directions link
    transformed_df["directions_url"] = transformed_df.apply(
        lambda row: f"https://www.google.com/maps/dir/{quote_plus(row.start_address_line)}/{quote_plus(row.address_line)}",
        axis=1,
    )

    # transform datetime
    transformed_df["exam_start_german_time"] = transformed_df["exam_start"].dt.strftime("%d.%m.%Y %H:%M")

    # drop all columns that are not translated
    cols_to_drop = list(set(transformed_df) - set(german_mapping))
    transformed_df.drop(cols_to_drop, axis=1, inplace=True)

    # rename the columns
    transformed_df.rename(columns=german_mapping, inplace=True)

    # reorder the columns
    transformed_df = transformed_df[german_mapping.values()]

    return transformed_df


def get_distance_from_gmaps(start_address: str, end_address: str) -> dict:
    gmaps = googlemaps.Client(key=setting.GMAP_API_KEY)
    directions_result = gmaps.directions(start_address, end_address)  # type: ignore # directions is member of gmaps
    return directions_result


def notify_admin_via_gchat(message: str) -> None:
    logger.info(f"Sending message to admin via gchat: {message[:40]}{'...' if len(message) > 40 else ''}")
    requests.post(setting.GCHAT_WEBHOOK_URL, json={"text": message})
