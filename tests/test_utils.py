import unittest
from datetime import datetime
from urllib.parse import quote_plus

import pandas as pd
from pytz import timezone
from sqlmodel import Session

from fishing_exam_alert import db, utils
from tests.utils import create_random_exam


class TestDateTimeUtils(unittest.TestCase):
    def test_localize_datetime(self):
        now = datetime.now()
        local_now = utils.localize_datetime(now)

        self.assertTrue(local_now != now)


class TestUtils(unittest.TestCase):
    def test_transform_db_dataframe_for_mail(self):
        exam_start = utils.localize_datetime(datetime.now())

        with Session(db.engine) as session:
            test_exam = create_random_exam(session, exam_start=exam_start)
            test_exam_address_line = test_exam.get_address_line()

        df = pd.DataFrame.from_records(
            data=[
                {
                    **test_exam.dict(),
                    "address_line": test_exam_address_line,
                }
            ]
        )

        transformed_df = utils.transform_db_dataframe_for_mail(df)

        self.assertTrue(len(transformed_df) == 1)

        first_row = transformed_df.iloc[0]
        self.assertTrue(first_row["Adresse"] == test_exam_address_line)
        localized_exam_start = utils.localize_datetime(test_exam.exam_start)
        self.assertTrue(first_row["Prüfungsbeginn"] == localized_exam_start.strftime("%d.%m.%Y %H:%M"))
        self.assertTrue(
            first_row["Belegte Plätze"] == f"{test_exam.current_participants} / {test_exam.max_participants}"
        )

    def test_transform_db_dataframe_for_mail_with_destination(self):
        with Session(db.engine) as session:
            test_exam = create_random_exam(session)

        df = pd.DataFrame.from_records(
            data=[
                {
                    **test_exam.dict(),
                    "start_address_line": "80469, Deutschland",
                    "address_line": test_exam.get_address_line(),
                    "travel_duration": 90,
                    "travel_distance": 1000,
                }
            ]
        )

        transformed_df = utils.transform_db_dataframe_for_mail(df)

        self.assertTrue(len(transformed_df) == 1)

        first_row = transformed_df.iloc[0]
        self.assertTrue(first_row["Adresse"] == test_exam.get_address_line())
        localized_exam_start = utils.localize_datetime(test_exam.exam_start)
        self.assertTrue(first_row["Prüfungsbeginn"] == localized_exam_start.strftime("%d.%m.%Y %H:%M"))
        self.assertTrue(first_row["Entfernung Fahrzeit [min]"] == 1)
        self.assertTrue(first_row["Entfernung [km]"] == 1)
        self.assertTrue(
            first_row["Belegte Plätze"] == f"{test_exam.current_participants} / {test_exam.max_participants}"
        )
        self.assertTrue(
            first_row["Route"]
            == f"https://www.google.com/maps/dir/{quote_plus('80469, Deutschland')}/{quote_plus(test_exam.get_address_line())}"
        )
