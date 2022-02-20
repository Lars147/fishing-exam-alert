import time

from fishing_exam_alert import models, utils
from fishing_exam_alert.settings import setting


def main():
    """
    Will send the subscription / unsubscription emails and will mark this in the Google Sheet.
    """
    gsheet = models.GSheetTable(setting.GSHEET_SPREADSHEET_ID)

    not_notified_row_index = gsheet.get_index_of_first_not_notified_record()
    if not_notified_row_index < 0:
        print("No records found that need to be notified. Exiting script...")
        return
    print(f"Run notification script for index {not_notified_row_index}...")

    row_to_notify = gsheet.df.iloc[not_notified_row_index]

    notification_row = gsheet.transform_row_to_notify_dict(row_to_notify)

    # send mail
    if row_to_notify["An- oder Abmeldung?"] == "Anmeldung / Aktualisierung":
        print(f"Send confirmation mail to {notification_row['email_notify']}...")
        utils.send_confirmation_mail(notification_row["email_notify"], notification_row["filters"])
    elif row_to_notify["An- oder Abmeldung?"] == "Abmeldung":
        print(f"Send unsubscribe mail to {notification_row['email_notify']}...")
        utils.send_unsubscribe_mail(notification_row["email_notify"])
    else:
        print(f"Unknown value for An- oder Abmeldung?: {row_to_notify['An- oder Abmeldung?']}")

    gsheet.mark_row_as_notified(not_notified_row_index)


if __name__ == "__main__":
    while True:
        main()
        time.sleep(5)
