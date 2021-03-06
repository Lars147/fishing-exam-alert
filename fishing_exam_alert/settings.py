import os


class Settings:
    CONFIRMATION_INTERVAL_SECONDS: int = int(os.getenv("CONFIRMATION_INTERVAL_SECONDS", "10"))
    RUN_INTERVAL_MINUTES: int = int(os.getenv("RUN_INTERVAL_MINUTES", "60"))
    EXAM_SCRAP_URL: str = (
        os.environ.get("EXAM_SCRAP_URL") or "https://fischerpruefung-online.bayern.de/fprApp/verwaltung/Pruefungssuche"
    )
    GMAP_API_KEY: str = os.environ["GMAP_API_KEY"]
    GSHEET_SPREADSHEET_ID: str = os.environ["GSHEET_SPREADSHEET_ID"]
    SUBSCRIBE_URL: str = os.environ["SUBSCRIBE_URL"]
    UNSUBSCRIBE_URL: str = os.environ["UNSUBSCRIBE_URL"]
    MAIL_SERVICE: str = os.environ["MAIL_SERVICE"]  # either GMX or mailersend
    NOTIFY_MAIL_FROM: str = os.environ["NOTIFY_MAIL_FROM"]
    NOTIFY_MAIL_REPLY_TO: str = os.getenv("NOTIFY_MAIL_REPLY_TO", "")  # optional: reply_to mail address
    NOTIFY_MAIL_PASSWORD: str = os.environ["NOTIFY_MAIL_PASSWORD"]

    # for admin
    DISTANCE_THRESHOLD: int = int(os.getenv("DISTANCE_THRESHOLD", "500"))
    GCHAT_WEBHOOK_URL: str = os.environ["GCHAT_WEBHOOK_URL"]

    # for testing
    TEST_EMAIL: str = os.environ.get("TEST_EMAIL", "")

    def __init__(self):
        self.validate()

    def validate(self) -> None:
        # validate the mail service
        allowed_mail_services = ["GMX", "mailersend"]
        if self.MAIL_SERVICE not in allowed_mail_services:
            raise ValueError(f"MAIL_SERVICE must be one of {allowed_mail_services}; not {self.MAIL_SERVICE}!")


setting = Settings()
