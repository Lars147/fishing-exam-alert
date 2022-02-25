import time

from sqlmodel import Session

from fishing_exam_alert import db, models, utils
from fishing_exam_alert.settings import setting


def sync_users_from_gsheet(gsheet: models.GSheetTable):
    active_notifications = gsheet.get_active_records()
    emails = active_notifications["E-Mail-Adresse"]
    
    with Session(db.engine) as session:
        for mail in emails:
            models.User.get_or_create(session, email=mail)


def run():
    # get gsheet data
    gsheet = models.GSheetTable(setting.GSHEET_SPREADSHEET_ID)
    sync_users_from_gsheet(gsheet)
    active_notifications = gsheet.get_active_records()
    notifications = gsheet.transform_df_to_notify_rows(active_notifications)

    if not len(notifications):
        print("No active records found. Exiting run script...")
        return

    print(f"{len(notifications)} active records found!")

    # get the website and put it into a class that handles it
    exam_scraper = models.ExamTableScraper()

    for notification in notifications:
        print(f"Checking exams for {notification['email_notify']}...")
        filtered_exams = exam_scraper.get_exams(**notification["filters"])
        exams_count = len(filtered_exams)
        print(f"Found {exams_count} exam matches!")
        if exams_count:
            email_to_notify = notification["email_notify"]
            print(f"Notify {email_to_notify}...")
            utils.notify(email_to_notify, filtered_exams)


if __name__ == "__main__":
    db.SQLModel.metadata.create_all(db.engine)  # init db
    while True:
        run()
        minutes_to_sleep = 60 * setting.RUN_INTERVAL_MINUTES
        print(f"Sleeping for {minutes_to_sleep} minutes...")
        time.sleep(minutes_to_sleep)
