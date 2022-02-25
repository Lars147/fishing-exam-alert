import enum
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import gspread
import pandas as pd
import requests
import sqlmodel
from bs4 import BeautifulSoup
from gspread import Spreadsheet
from loguru import logger
from pandas import DataFrame
from requests import Response
from sqlalchemy import types
from sqlmodel.sql.expression import Select, SelectOfScalar

from fishing_exam_alert import utils
from fishing_exam_alert.settings import setting

DIRNAME = os.path.dirname(__file__)

# ignore SAWarnings
SelectOfScalar.inherit_cache = True  # type: ignore
Select.inherit_cache = True  # type: ignore


class District(str, enum.Enum):
    Oberbayern = "Oberbayern"
    Niederbayern = "Niederbayern"
    Schwaben = "Schwaben"
    Oberpfalz = "Oberpfalz"
    Unterfranken = "Unterfranken"
    Mittelfranken = "Mittelfranken"
    Oberfranken = "Oberfranken"


class User(sqlmodel.SQLModel, table=True):
    id: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
    email: str = sqlmodel.Field(sa_column=sqlmodel.Column("email", sqlmodel.String, unique=True))
    districts: Optional[str] = ""
    postal_code: Optional[str] = ""
    active: bool = True
    created_at: Optional[datetime] = sqlmodel.Field(
        sa_column=sqlmodel.Column(
            sqlmodel.DateTime,
            default=datetime.utcnow,
            nullable=False,
        )
    )
    updated_at: Optional[datetime] = sqlmodel.Field(
        sa_column=sqlmodel.Column(
            sqlmodel.DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        )
    )

    @property
    def district_list(self) -> List[District]:
        if not self.districts:
            return []
        return [District(d.strip()) for d in self.districts.split(",")]

    @classmethod
    def get(cls, db: sqlmodel.Session, id: int) -> "User":
        statement = sqlmodel.select(cls).where(cls.id == id)
        results = db.exec(statement)
        return results.one()

    @classmethod
    def delete(cls, db: sqlmodel.Session, id: int) -> bool:
        user = cls.get(db, id=id)
        if user:
            db.delete(user)
            return True
        return False

    @classmethod
    def get_or_create(cls, db: sqlmodel.Session, email: str, defaults: Dict[str, Any] = {}) -> Tuple["User", bool]:
        user = cls.get_by_mail(db, email=email)
        created = False
        if not user:
            user = cls(email=email)
            if defaults:
                for k, v in defaults.items():
                    setattr(user, k, v)
            db.add(user)
            db.commit()
            created = True
        return user, created

    @classmethod
    def update_or_create(cls, db: sqlmodel.Session, email: str, defaults: Dict[str, Any] = {}) -> Tuple["User", bool]:
        user, created = cls.get_or_create(db, email=email, defaults=defaults)
        if not created:
            for k, v in defaults.items():
                setattr(user, k, v)
            db.add(user)
            db.commit()
        return user, created

    @classmethod
    def get_by_mail(cls, db: sqlmodel.Session, email: str) -> Optional["User"]:
        statement = sqlmodel.select(cls).where(cls.email == email)
        results = db.exec(statement)
        return results.first()

    @classmethod
    def get_multi_by_active(cls, db: sqlmodel.Session, active: bool) -> List["User"]:
        statement = sqlmodel.select(cls).where(cls.active == active)
        results = db.exec(statement)
        return results.all()

    def create_email_log(self, db: sqlmodel.Session, category: "EmailLogCategory", content: str) -> None:
        mail = EmailLog(category=category, content=content, user_id=self.id)
        db.add(mail)
        db.commit()


class EmailLogCategory(str, enum.Enum):
    subscribe = "subscribe"
    unsubscribe = "unsubscribe"
    notification = "notification"


class EmailLog(sqlmodel.SQLModel, table=True):
    id: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
    category: EmailLogCategory = sqlmodel.Field(sa_column=sqlmodel.Column(types.Enum(EmailLogCategory)))
    content: str
    created_at: Optional[datetime] = sqlmodel.Field(
        sa_column=sqlmodel.Column(
            sqlmodel.DateTime,
            default=datetime.utcnow,
            nullable=False,
        )
    )
    user_id: Optional[int] = sqlmodel.Field(default=None, foreign_key="user.id")

    @classmethod
    def get_latest_mail_by_user_mail(cls, db: sqlmodel.Session, email: str) -> Optional["EmailLog"]:
        user = User.get_by_mail(db, email=email)
        if not user:
            return
        statement = sqlmodel.select(cls).where(cls.user_id == user.id).order_by(cls.created_at.desc()).limit(1)
        results = db.exec(statement)
        return results.first()


class Exam(sqlmodel.SQLModel, table=True):
    """A fishing license exam.

    This model is mapped to the values of the "printing view" of
    https://fischerpruefung-online.bayern.de/fprApp/verwaltung/Pruefungssuche.
    """

    id: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
    exam_id: str
    name: str
    street: str
    street_number: str
    city: str
    postal_code: str
    district: District
    exam_start: datetime
    min_participants: int
    max_participants: int
    current_participants: int
    status: str
    disabled_access: bool
    headphones: bool
    created_at: Optional[datetime] = sqlmodel.Field(
        sa_column=sqlmodel.Column(
            sqlmodel.DateTime,
            default=datetime.utcnow,
            nullable=False,
        )
    )
    updated_at: Optional[datetime] = sqlmodel.Field(
        sa_column=sqlmodel.Column(
            sqlmodel.DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        )
    )

    @classmethod
    def get_exam_by_exam_id(cls, db: sqlmodel.Session, exam_id: str) -> Optional["Exam"]:
        statement = sqlmodel.select(cls).where(cls.exam_id == exam_id)
        results = db.exec(statement)
        return results.first()

    @classmethod
    def get_or_create(cls, db: sqlmodel.Session, exam_id: str, defaults: dict = {}) -> "Exam":
        exam = cls.get_exam_by_exam_id(db, exam_id=exam_id)
        if not exam:
            exam = cls(exam_id=exam_id)
            if defaults:
                for k, v in defaults.items():
                    setattr(exam, k, v)
            db.add(exam)
            db.commit()
        return exam

    @classmethod
    def get_multi_as_dataframe(
        cls,
        db: sqlmodel.Session,
        status: Optional[str] = None,
        exam_start__min: Optional[datetime] = None,
        districts__in: Optional[List[District]] = None,
    ) -> DataFrame:
        statement = cls.get_multi_statement(
            status=status,
            exam_start__min=exam_start__min,
            districts__in=districts__in,
        )
        return pd.read_sql(statement, db.connection())

    @classmethod
    def get_multi(
        cls,
        db: sqlmodel.Session,
        status: Optional[str] = None,
        exam_start__min: Optional[datetime] = None,
        districts__in: Optional[List[District]] = None,
    ) -> List[Optional["Exam"]]:
        statement = cls.get_multi_statement(
            status=status,
            exam_start__min=exam_start__min,
            districts__in=districts__in,
        )

        results = db.exec(statement)
        return results.all()

    @classmethod
    def get_multi_statement(
        cls,
        status: Optional[str] = None,
        exam_start__min: Optional[datetime] = None,
        districts__in: Optional[List[District]] = None,
    ):
        statement = sqlmodel.select(cls)

        if status:
            statement = statement.where(cls.status == status)

        if exam_start__min:
            statement = statement.where(cls.exam_start >= exam_start__min)

        if districts__in:
            statement = statement.where(cls.district.in_(districts__in))

        return statement


class ExamUserDistance(sqlmodel.SQLModel, table=True):
    id: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
    distance: float
    duration: int
    user_id: Optional[int] = sqlmodel.Field(default=None, foreign_key="user.id")
    exam_id: Optional[int] = sqlmodel.Field(default=None, foreign_key="exam.id")


class ExamTableScraper:
    exam_url = setting.EXAM_SCRAP_URL
    exam_overview_response: Optional[requests.Response] = None
    exam_detail_response: Optional[requests.Response] = None
    exam_overview_columns: List[str] = ["", "Prüfungstermin", "Prüfungslokal", "Ort", "Regierungsbezirk", "Teilnehmer"]

    def __init__(self):
        self.set_responses()
        self.exams = self._parse_exam_tables()

    def get_exam_responses(self) -> List[Response]:
        # use a session to store cookie
        logger.info("Get exam responses...")

        responses = list()
        with requests.Session() as s:
            logger.info(f"Get cookie and CSRF-Token from {self.exam_url} ...")
            res_exam_url = s.get(self.exam_url)
            responses.append(res_exam_url)

            soup = BeautifulSoup(res_exam_url.content.decode("utf-8"), "html.parser")

            # get the CSRF-Token
            logger.debug("Search for cookie in response...")
            csrf_input_field = soup.find("input", {"name": "_csrf"})
            if not csrf_input_field:
                raise Exception("CSRF input field not found!")
            csrf_token = csrf_input_field["value"]
            logger.debug("Found cookie in response!")

            # get the printed view of the exam table (contains more info on exams)
            data = {
                "pruefungsterminSearch": "pruefungsterminSearch",
                "_csrf": csrf_token,
                "pruefungsterminSearch:j_idt190": "Druckansicht",
                "javax.faces.ViewState": "e1s1",
            }
            printed_res = s.post(f"{self.exam_url}?execution=e1s1", data=data)
            responses.append(printed_res)

        return responses

    def set_responses(self) -> None:
        self.exam_overview_response, self.exam_detail_response = self.get_exam_responses()

    def sync_exams_to_db(self, db: sqlmodel.Session) -> None:
        for exam in self.exams:
            exam_in = Exam.get_or_create(db, exam_id=exam.exam_id, defaults=exam.dict(exclude_unset=True))
            db.add(exam_in)
        db.commit()

    def _parse_exam_tables(self) -> List[Exam]:
        logger.info("Parse exam overview table...")
        soup_overview = BeautifulSoup(self.exam_overview_response.content.decode("utf-8"), "html.parser")
        overview_values = self._extract_overview_table(soup_overview)
        logger.info("Parsed exam overview table!")

        logger.info("Parse exam detail table...")
        soup = BeautifulSoup(self.exam_detail_response.content.decode("utf-8"), "html.parser")
        tables = soup.select("#pruefungverwaltung > div:nth-child(2) > div.rf-p-b > div > div.rf-p-b")
        logger.debug(f"Found {len(tables)} tables!")

        rows = list()
        for table in tables:
            raw_table_data = self._extract_detail_table(table)

            # get the district by exam overview table
            district = self._match_overview_table_row(overview_values, raw_table_data)

            # create exam datetime and localize it
            exam_start_str = f'{raw_table_data["Prüfungstermin"]} {raw_table_data["Prüfungsbeginn"]}'
            exam_start_dt = datetime.strptime(exam_start_str, "%d.%m.%Y %H:%M")
            exam_start = utils.localize_datetime(exam_start_dt)

            rows.append(
                Exam(
                    exam_id=raw_table_data["Prüfungs-Nr."],
                    name=raw_table_data["Prüfungslokal"],
                    street=raw_table_data["Straße"],
                    street_number=raw_table_data["Haus-Nr."],
                    city=raw_table_data["Ort"],
                    postal_code=raw_table_data["PLZ"],
                    district=district,
                    exam_start=exam_start,
                    min_participants=raw_table_data["Min. Teilnehmer"],
                    max_participants=raw_table_data["Max. Teilnehmer"],
                    current_participants=raw_table_data["Aktuelle Teilnehmer"],
                    status=raw_table_data["Status"],
                    disabled_access=bool(raw_table_data["Behindertengerecht"]),
                    headphones=bool(raw_table_data["Kopfhörer"]),
                )
            )
        return rows

    def _match_overview_table_row(self, overview_table: List[Dict[str, str]], detail_table: Dict[str, str]) -> District:
        for row in overview_table:
            if row["Prüfungslokal"] != detail_table["Prüfungslokal"]:
                continue
            if row["Ort"] != detail_table["Ort"]:
                continue
            if row["Prüfungstermin"] != f'{detail_table["Prüfungstermin"]}, {detail_table["Prüfungsbeginn"]}':
                continue
            return District(row["Regierungsbezirk"])
        raise Exception(f"Could not match row {detail_table}")

    def _extract_overview_table(self, table_soup: BeautifulSoup) -> List[Dict[str, str]]:
        exam_table_selector = "#pruefungsterminSearch\:pruefungsterminList > tbody > tr"
        table_rows = table_soup.select(exam_table_selector)
        print(f"Found {len(table_rows)} exams...")

        rows = list()
        for row in table_rows:
            rows.append(self._extract_table_row(row))
        return rows

    def _extract_table_row(self, row) -> Dict[str, str]:
        columns = row.select("td")
        table_row = dict()
        for name, col in zip(self.exam_overview_columns, columns):
            table_row[name] = col.text.strip()
        return table_row

    def _extract_detail_table(self, table_soup) -> Dict[str, str]:
        """Extract the details of an exam table"""
        table_names = table_soup.select(".prop > .name")
        table_values = table_soup.select(".prop > .value")
        table_row = dict()
        for name, value in zip(table_names, table_values):
            val = value.text.strip()
            if not val:
                try:
                    val = value.select(".checkbox")[0].get("checked", "")
                except KeyError as e:
                    val = None
            table_row[name.text.strip()] = val
        return table_row


class GSheetTable:
    notification_column_name = "__auto__notified"

    def __init__(self, gsheet_key: str, sheet_number: int = 0) -> None:
        self.gsheet_key = gsheet_key
        self.sheet_number = sheet_number
        self.gc = gspread.oauth(
            credentials_filename=os.path.join(DIRNAME, "google_creds/gsheet_credentials.json"),
            authorized_user_filename=os.path.join(DIRNAME, "google_creds/authorized_user.json"),
        )
        self.sheet = self.get_sheet()
        self.worksheet = self.sheet.get_worksheet(self.sheet_number)
        self.df = self.get_records_as_dataframe()

    def get_sheet(self) -> Spreadsheet:
        # TODO: test this
        sh = self.gc.open_by_key(self.gsheet_key)
        return sh

    def get_records_as_dataframe(self) -> DataFrame:
        df = pd.DataFrame(self.worksheet.get_all_records())

        df.drop(df[df["E-Mail-Adresse"] == ""].index, inplace=True)
        df.reset_index(inplace=True, drop=True)

        df["Zeitstempel"] = pd.to_datetime(df["Zeitstempel"])  # convert str to datetime

        # add column for notification state
        if self.notification_column_name not in df:
            df[self.notification_column_name] = "FALSE"

        # check that column has a default value for each row
        df[self.notification_column_name].replace("", "FALSE", inplace=True)

        return df

    def get_record_updates(self) -> DataFrame:
        update_df = self.df.copy()
        update_df = update_df.sort_values(by="Zeitstempel")
        update_df = update_df.drop_duplicates(subset=["E-Mail-Adresse"], keep="last")
        return update_df

    def get_active_records(self) -> DataFrame:
        """Keep only last record per unique "E-Mail-Adresse" and only if it is has the value "Anmeldung"."""
        active_df = self.get_record_updates()
        active_df = active_df[active_df["An- oder Abmeldung?"] == "Anmeldung / Aktualisierung"]
        return active_df

    def get_index_of_first_not_notified_record(self) -> int:
        index = self.df.index
        condition = self.df[self.notification_column_name] == "FALSE"
        not_notified_indices = index[condition]
        not_notified_indices_list = not_notified_indices.tolist()

        if not not_notified_indices_list:
            return -1

        return not_notified_indices_list[0]

    def mark_row_as_notified(self, row_index: int) -> None:
        print(f"Mark row {row_index} as notified...")
        self.df.loc[row_index, self.notification_column_name] = "TRUE"
        row_to_mark = self.df.iloc[row_index]

        print(
            f"Marking row {row_index} (E-Mail: {row_to_mark['E-Mail-Adresse']}; Zeitstempel: {row_to_mark['Zeitstempel']}) as notified..."
        )
        self.worksheet.clear()
        self.update()

    def get_not_notified_records(self) -> DataFrame:
        """Get all records that are not yet notified."""
        df = self.df[self.df[self.notification_column_name] == "FALSE"]
        return df

    def update(self) -> None:
        self.df["Zeitstempel"] = self.df["Zeitstempel"].dt.strftime("%d.%m.%Y %H:%M:%S")
        self.worksheet.update([self.df.columns.values.tolist()] + self.df.values.tolist())

    def refresh(self) -> None:
        """Will get the latest data from the sheet."""
        self.sheet = self.get_sheet()
        self.worksheet = self.sheet.get_worksheet(self.sheet_number)
        self.df = self.get_records_as_dataframe()

    def remove_old_records(self) -> None:
        """Overwrites the sheet with only active records"""
        cleaned_df = self.get_active_records()
        self.df = cleaned_df
        self.worksheet.clear()
        self.update()

    @staticmethod
    def transform_row_to_notify_dict(row) -> dict:
        """
        A notification row is a dict that looks like this:
        ```
        {
            "filters":
            {
                "Teilnehmer": "Frei",
                "Regierungsbezirk": ["Oberbayern"]
            },
            "email_notify": "larsheinen@gmail.com"
        }
        ```
        """
        notify_row = dict()

        # add email
        notify_row["email_notify"] = row["E-Mail-Adresse"]

        # add filters
        notify_row["filters"] = dict()
        notify_row["filters"]["Teilnehmer"] = "Frei"
        locations = row["Nur bestimmte Regierungsbezirke? (Standard: Alle)"]
        if locations:
            notify_row["filters"]["Regierungsbezirk"] = locations.split(", ")

        return notify_row

    def transform_df_to_notify_rows(self, records: DataFrame) -> List[dict]:
        """
        Convert records to a list of notification rows.
        """
        notify_rows = list()

        for idx, row in records.iterrows():
            notify_row = self.transform_row_to_notify_dict(row)
            notify_rows.append(notify_row)

        return notify_rows
