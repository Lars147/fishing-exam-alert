import os


class Settings:
    GSHEET_SPREADSHEET_ID: str = os.environ["GSHEET_SPREADSHEET_ID"]
    NOTIFY_MAIL_FROM: str = os.environ["NOTIFY_MAIL_FROM"]
    NOTIFY_MAIL_PASSWORD: str = os.environ["NOTIFY_MAIL_PASSWORD"]


setting = Settings()
