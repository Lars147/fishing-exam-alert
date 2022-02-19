import os
from typing import List

import gspread
import pandas as pd
import requests
from bs4 import BeautifulSoup
from gspread import Spreadsheet
from pandas import DataFrame
from requests import Response

DIRNAME = os.path.dirname(__file__)


class ExamTableScraper:
    exam_url = "https://fischerpruefung-online.bayern.de/fprApp/verwaltung/Pruefungssuche"
    exam_table_selector = "#pruefungsterminSearch\:pruefungsterminList > tbody > tr"
    exam_result_size_selector = "#pruefungsterminSearch > div.tableControl > span.resultSize"
    exam_table_columns = ["", "Datum", "Prüfungslokal", "Ort", "Regierungsbezirk", "Teilnehmer"]

    def __init__(self):
        self._exam_response = self.get_exam_response()
        self.exam_response_content = self.exam_response.content.decode("utf-8")
        self.exam_rows = self._parse_exam_table()
        self.exams_result_size = self._parse_result_size()  # e.g. ['1', '-', '36', 'von', '36']

    @property
    def exam_response(self) -> Response:
        return self._exam_response

    def get_exam_response(self) -> Response:
        print(f"Get exams from {self.exam_url} ...")
        res = requests.get(self.exam_url)
        return res

    def get_exams(self, **filter_queries):
        filtered_exams = self.exam_rows  # init with all rows

        for field_name, search_value in filter_queries.items():

            if field_name not in self.exam_table_columns:
                raise ValueError(f"Field name '{field_name}' is not a valid column name!")

            filtered_exams = [row for row in filtered_exams if row[field_name] == search_value]

        return filtered_exams

    def has_all_results(self) -> bool:
        if len(self.exams_result_size) == 5:
            return False
        return self.exams_result_size[2] == self.exams_result_size[4]

    def _parse_result_size(self) -> list:
        soup = BeautifulSoup(self.exam_response_content, "html.parser")

        result_size_selection = soup.select(self.exam_result_size_selector)
        if not result_size_selection:
            return []

        result_size_string = result_size_selection[0].string
        if not result_size_string:
            return []

        result_size = result_size_string.split("\n")
        return [t.strip() for t in result_size if t.strip()]

    def _parse_exam_table(self) -> List[dict]:
        soup = BeautifulSoup(self.exam_response_content, "html.parser")

        table_rows = soup.select(self.exam_table_selector)
        print(f"Found {len(table_rows)} exams...")

        rows = list()
        for row in table_rows:
            rows.append(self._extract_table_row(row))
        return rows

    def _extract_table_row(self, row) -> dict:
        columns = row.select("td")
        table_row = dict()
        for name, col in zip(self.exam_table_columns, columns):
            table_row[name] = col.text
        return table_row


class GSheetTable:
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
        df["Zeitstempel"] = pd.to_datetime(df["Zeitstempel"])
        return df

    def get_active_records(self) -> DataFrame:
        """Keep only last record per unique "E-Mail-Adresse" and only if it is has the value "Anmeldung"."""
        active_df = self.df.copy()
        active_df = active_df.sort_values(by="Zeitstempel")
        active_df = active_df.drop_duplicates(subset=["E-Mail-Adresse"], keep="last")
        active_df = active_df[active_df["An- oder Abmeldung?"] == "Anmeldung / Aktualisierung"]
        return active_df

    def get_active_records_starting_now(self) -> DataFrame:
        active_df = self.get_active_records()
        active_df_starting_now = active_df[active_df["Zeitstempel"] <= pd.Timestamp.now()]
        return active_df_starting_now

    def remove_old_records(self) -> None:
        """Overwrites the sheet with only active records"""
        cleaned_df = self.get_active_records()
        cleaned_df["Zeitstempel"] = cleaned_df["Zeitstempel"].dt.strftime("%d.%m.%Y %H:%M:%S")
        self.worksheet.clear()
        self.worksheet.update([cleaned_df.columns.values.tolist()] + cleaned_df.values.tolist())

    @staticmethod
    def transform_df_to_notify_rows(records: DataFrame) -> List[dict]:
        """
        Convert records to a list of notification rows.

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
        notify_rows = list()

        for idx, row in records.iterrows():
            notify_row = dict()

            # add email
            notify_row["email_notify"] = row["E-Mail-Adresse"]

            # add filters
            notify_row["filters"] = dict()
            notify_row["filters"]["Teilnehmer"] = "Frei"
            locations = row["Nur bestimmte Regierungsbezirke? (Standard: Alle)"]
            if locations:
                notify_row["filters"]["Regierungsbezirk"] = locations.split(", ")

            notify_rows.append(notify_row)

        return notify_rows
