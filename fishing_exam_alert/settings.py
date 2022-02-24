import os


class Settings:
    EXAM_SCRAP_URL: str = (
        os.environ.get("EXAM_SCRAP_URL") or "https://fischerpruefung-online.bayern.de/fprApp/verwaltung/Pruefungssuche"
    )
    GSHEET_SPREADSHEET_ID: str = os.environ["GSHEET_SPREADSHEET_ID"]
    SUBSCRIBE_URL: str = os.environ["SUBSCRIBE_URL"]
    UNSUBSCRIBE_URL: str = os.environ["UNSUBSCRIBE_URL"]
    MAIL_SERVICE: str = os.environ["MAIL_SERVICE"]  # either GMX or mailersend
    NOTIFY_MAIL_FROM: str = os.environ["NOTIFY_MAIL_FROM"]
    NOTIFY_MAIL_REPLY_TO: str = os.getenv("NOTIFY_MAIL_REPLY_TO", "")  # optional: reply_to mail address
    NOTIFY_MAIL_PASSWORD: str = os.environ["NOTIFY_MAIL_PASSWORD"]

    def __init__(self):
        self.validate()

    def validate(self) -> None:
        # validate the mail service
        allowed_mail_services = ["GMX", "mailersend"]
        if self.MAIL_SERVICE not in allowed_mail_services:
            raise ValueError(f"MAIL_SERVICE must be one of {allowed_mail_services}; not {self.MAIL_SERVICE}!")


setting = Settings()
