import unittest

from sqlmodel import Session

from fishing_exam_alert import db, models
from tests.utils import create_random_user


class TestUser(unittest.TestCase):
    def test_get_or_create_user_does_not_exist(self):
        with Session(db.engine) as session:
            user = create_random_user(session)

        self.assertEqual(isinstance(user, models.User), True)

    def test_get_or_create_user_exists(self):
        with Session(db.engine) as session:
            user = create_random_user(session)
            user_in, _ = models.User.get_or_create(session, email=user.email)

        self.assertEqual(user_in, user)

    def test_districts(self):
        districts = [models.District.Mittelfranken, models.District.Oberbayern]

        with Session(db.engine) as session:
            user = create_random_user(session, districts=", ".join([d.value for d in districts]))

            self.assertEqual(user.district_list, districts)
