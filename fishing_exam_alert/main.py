import time

from fishing_exam_alert import models, utils
from fishing_exam_alert.settings import setting

from db import engine, SQLModel


def run():
    # get gsheet data
    gsheet = models.GSheetTable(setting.GSHEET_SPREADSHEET_ID)
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
    SQLModel.metadata.create_all(engine)    # init db
    while True:
        run()
        print("Sleeping for 1 hour...")
        time.sleep(60 * 60 * 1)
