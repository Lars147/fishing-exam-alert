import unittest
from datetime import datetime

from sqlmodel import Session
from utils import create_random_exam, create_random_user

from fishing_exam_alert import db, main, models, utils


class TestMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with Session(db.engine) as session:
            exams = models.Exam.get_multi(session)
            for exam in exams:
                session.delete(exam)
            session.commit()

    def test_get_active_exams_with_duration(self):

        exam_start = utils.localize_datetime(datetime.now())

        with Session(db.engine) as session:
            test_user = create_random_user(session, need_headphones=False, need_disabled_access=False, active=True)
            test_exam = create_random_exam(session, exam_id="0001", exam_start=exam_start)

            active_exams = main.get_active_exams(session, test_user)

        self.assertEqual(len(active_exams), 1)
        self.assertEqual(active_exams.iloc[0]["exam_id"], test_exam.exam_id)
        self.assertEqual(active_exams.iloc[0]["address_line"], test_exam.get_address_line())
        self.assertEqual(active_exams.iloc[0]["travel_distance"] > 0, True)
        self.assertEqual(active_exams.iloc[0]["travel_duration"] > 0, True)

        active_exam_dt = active_exams.iloc[0]["exam_start"]
        self.assertEqual(active_exam_dt.isoformat(), exam_start.isoformat())
