import os


class Settings:
    EXAM_SCRAP_URL: str = (
        os.environ.get("EXAM_SCRAP_URL") or "https://fischerpruefung-online.bayern.de/fprApp/verwaltung/Pruefungssuche"
    )
    GSHEET_SPREADSHEET_ID: str = os.environ["GSHEET_SPREADSHEET_ID"]
    SUBSCRIBE_URL: str = os.environ["SUBSCRIBE_URL"]
    UNSUBSCRIBE_URL: str = os.environ["UNSUBSCRIBE_URL"]
    NOTIFY_MAIL_FROM: str = os.environ["NOTIFY_MAIL_FROM"]
    NOTIFY_MAIL_PASSWORD: str = os.environ["NOTIFY_MAIL_PASSWORD"]


setting = Settings()
