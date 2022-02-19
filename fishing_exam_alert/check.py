from fishing_exam_alert.models import GSheetTable
from fishing_exam_alert.settings import setting
from fishing_exam_alert.utils import send_mail


def get_length_of_gsheet() -> int:
    gsheet = GSheetTable(setting.GSHEET_SPREADSHEET_ID)
    return gsheet.worksheet.row_count


def send_test_mail(subject: str = "") -> None:
    if subject:
        send_mail(setting.NOTIFY_MAIL_FROM, subject, "Test")
    else:
        send_mail(setting.NOTIFY_MAIL_FROM, "Test", "Test")


if __name__ == "__main__":
    print("Check access to GSheet...", end="")
    gsheet_len = get_length_of_gsheet()
    print("Done!")
    print("Send mail via GMX...", end="")
    send_test_mail(subject=f"This is a test! GSheet has {gsheet_len} rows!")
    print("Done!")
