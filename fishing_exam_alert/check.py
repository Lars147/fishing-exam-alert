from loguru import logger

from fishing_exam_alert.models import GSheetTable
from fishing_exam_alert.notifier import send_confirmation_mail, send_mail
from fishing_exam_alert.settings import setting


def get_length_of_gsheet() -> int:
    gsheet = GSheetTable(setting.GSHEET_SPREADSHEET_ID)
    return gsheet.worksheet.row_count


def send_test_mail(subject: str = "") -> None:
    if subject:
        send_mail(setting.NOTIFY_MAIL_FROM, subject, "Test")
    else:
        send_mail(setting.NOTIFY_MAIL_FROM, "Test", "Test")


if __name__ == "__main__":
    logger.info("Check access to GSheet...", end="")
    gsheet_len = get_length_of_gsheet()
    logger.info("Done!")

    logger.info("Send mail via GMX...", end="")
    send_test_mail(subject=f"This is a test! GSheet has {gsheet_len} rows!")
    logger.info("Done!")

    logger.info("Send test confirmation mail via GMX...", end="")
    test_filters = {"Teilnehmer": "Frei", "Regierungsbezirk": ["Oberbayern"]}
    send_confirmation_mail(setting.NOTIFY_MAIL_FROM, test_filters)
    logger.info("Done!")
