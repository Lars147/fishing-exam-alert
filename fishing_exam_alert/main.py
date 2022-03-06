import time
from datetime import datetime

import pandas as pd
from loguru import logger
from sqlmodel import Session

from fishing_exam_alert import db, models, notifier, utils
from fishing_exam_alert.settings import setting


def sync_users_from_gsheet() -> None:
    gsheet = models.GSheetTable(setting.GSHEET_SPREADSHEET_ID)
    user_updates = gsheet.get_record_updates()

    with Session(db.engine) as session:
        for _, row in user_updates.iterrows():
            active = row["An- oder Abmeldung?"] == "Anmeldung / Aktualisierung"
            defaults = {
                "active": active,
                "districts": row["Welche Bezirke kommen für dich in Frage?"],
                "max_travel_duration": int(row["Maximale Fahrzeit zur Prüfung (in Minuten)?"] or "0"),
                "postal_code": row["Deine PLZ"],
                "need_headphones": "Kopfhörer" in row["Welche Ausstattung soll der Prüfungsort erfüllen?"],
                "need_disabled_access": "Behindertengerecht"
                in row["Welche Ausstattung soll der Prüfungsort erfüllen?"],
            }
            models.User.update_or_create(session, email=row["E-Mail-Adresse"], defaults=defaults)


def sync_exams() -> None:
    exam_scraper = models.ExamTableScraper()
    with Session(db.engine) as session:
        exam_scraper.sync_exams_to_db(session)


def get_active_exams(db: Session, user: models.User) -> pd.DataFrame:
    # filter the exams for the user settings
    filtered_exams = models.Exam.get_multi(
        db=db,
        status="Frei",
        exam_start__min=datetime.utcnow(),
        districts__in=user.district_list or None,
        disabled_access=user.need_disabled_access or None,
        headphones=user.need_headphones or None,
    )

    filtered_exams_localized = list()
    for f in filtered_exams:
        f.exam_start = utils.localize_datetime(f.exam_start)
        filtered_exams_localized.append(f)

    # check if the user wants the exams filtered by travel duration
    exams_for_user = list()
    if user.max_travel_duration and user.get_address_line():

        for exam in filtered_exams_localized:
            distance_in, _ = models.Distance.get_or_create(
                db, start_address=user.get_address_line(), end_address=exam.get_address_line()
            )
            travel_duration = distance_in.get_duration(db=db)
            travel_distance = distance_in.get_distance(db=db)

            # if the duration is smaller than the user's max travel duration, add the exam to the list
            cutoff_travel_duration_for_user_in_minutes = user.max_travel_duration + 10  # 10 minutes buffer
            if travel_duration < cutoff_travel_duration_for_user_in_minutes * 60:  # for comparison convert to seconds
                exams_for_user.append(
                    exam.dict()
                    | {
                        "start_address_line": user.get_address_line(),
                        "address_line": exam.get_address_line(),
                        "travel_duration": travel_duration,
                        "travel_distance": travel_distance,
                    }
                )
    else:
        exams_for_user = [exam.dict() | {"address_line": exam.get_address_line()} for exam in filtered_exams]

    return pd.DataFrame.from_records(exams_for_user)


def run():
    sync_users_from_gsheet()
    sync_exams()

    with Session(db.engine) as session:
        active_users = models.User.get_multi_by_active(db=session, active=True)

    if not len(active_users):
        logger.info("No active users found. Exiting run script...")
        return

    for user in active_users:

        logger.debug(f"Get exams for user {user.email}...")
        with Session(db.engine) as session:
            active_exams = get_active_exams(session, user)

        logger.debug(f"Found {len(active_exams)} exam matches!")
        if len(active_exams):
            logger.info(f"Notify {user.email}...")
            mail_friendly_exams = utils.transform_db_dataframe_for_mail(active_exams)
            notifier.notify(user.email, mail_friendly_exams)


if __name__ == "__main__":
    db.SQLModel.metadata.create_all(db.engine)  # init db
    while True:
        try:
            run()
            utils.notify_admin_via_gchat(f"Fishing Exam Alert: Successfully ran script at {datetime.now()}")
        except Exception as e:
            utils.notify_admin_via_gchat(f"<users/all> An error occurred:\n\n{e}")
            raise e

        logger.info(f"Sleeping for {setting.RUN_INTERVAL_MINUTES} minutes...")
        time.sleep(60 * setting.RUN_INTERVAL_MINUTES)  # sleep in seconds
