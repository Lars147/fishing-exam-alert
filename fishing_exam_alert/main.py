import time
from datetime import datetime

from loguru import logger
from sqlmodel import Session

from fishing_exam_alert import db, models, notifier, utils
from fishing_exam_alert.settings import setting


def sync_users_from_gsheet() -> None:
    gsheet = models.GSheetTable(setting.GSHEET_SPREADSHEET_ID)
    user_updates = gsheet.get_record_updates()

    with Session(db.engine) as session:
        for idx, row in user_updates.iterrows():
            active = row["An- oder Abmeldung?"] == "Anmeldung / Aktualisierung"
            defaults = {"active": active}
            models.User.update_or_create(session, email=row["E-Mail-Adresse"], defaults=defaults)


def sync_exams() -> None:
    exam_scraper = models.ExamTableScraper()
    with Session(db.engine) as session:
        exam_scraper.sync_exams_to_db(session)


def run():
    sync_users_from_gsheet()
    sync_exams()

    with Session(db.engine) as session:
        active_users = models.User.get_multi_by_active(db=session, active=True)

    if not len(active_users):
        logger.info("No active users found. Exiting run script...")
        return

    for user in active_users:
        logger.debug("Get exams for user...")
        with Session(db.engine) as session:
            active_exams = models.Exam.get_multi_as_dataframe(
                db=session, status="Frei", exam_start__min=datetime.utcnow(), districts__in=user.district_list
            )
        logger.debug(f"Found {len(active_exams)} exam matches!")
        if len(active_exams):
            logger.info(f"Notify {user.email}...")
            mail_friendly_exams = utils.transform_db_dataframe_for_mail(active_exams)
            notifier.notify(user.email, mail_friendly_exams)


if __name__ == "__main__":
    db.SQLModel.metadata.create_all(db.engine)  # init db
    while True:
        run()
        minutes_to_sleep = 60 * setting.RUN_INTERVAL_MINUTES
        print(f"Sleeping for {setting.RUN_INTERVAL_MINUTES} minutes...")
        time.sleep(minutes_to_sleep)
