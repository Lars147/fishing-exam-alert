import unittest

from sqlmodel import Session
from utils import create_random_exam, create_random_user

from fishing_exam_alert import db, main


class TestMain(unittest.TestCase):
    def test_get_active_exams_with_duration(self):
        with Session(db.engine) as session:
            test_user = create_random_user(session)
            test_exam = create_random_exam(session)

            active_exams = main.get_active_exams(session, test_user)

        self.assertTrue(len(active_exams) == 1)
        self.assertTrue(active_exams.iloc[0]["exam_id"] == test_exam.exam_id)
        self.assertTrue(active_exams.iloc[0]["address_line"] > test_user.get_address_line())
        self.assertTrue(active_exams.iloc[0]["travel_distance"] > 0)
        self.assertTrue(active_exams.iloc[0]["travel_duration"] > 0)
