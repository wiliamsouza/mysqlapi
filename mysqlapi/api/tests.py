from django.test import TestCase
from django.db import connection
from django.test.client import RequestFactory
from django.utils import simplejson

from mysqlapi.api.models import DatabaseManager
from mysqlapi.api.views import create, drop


class DatabaseViewTestCase(TestCase):

    def setUp(self):
        self.cursor = connection.cursor()

    def test_create_should_returns_405_when_method_is_not_post(self):
        request = RequestFactory().get("/")
        response = create(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = create(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().delete("/")
        response = create(request)
        self.assertEqual(405, response.status_code)

    def test_drop_should_returns_405_when_method_is_not_delete(self):
        request = RequestFactory().get("/")
        response = drop(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = drop(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().post("/")
        response = drop(request)
        self.assertEqual(405, response.status_code)

    def test_create(self):
        request = RequestFactory().post("/", {"appname": "ciclops"})
        response = create(request)
        self.assertEqual(201, response.status_code)
        content = simplejson.loads(response.content)
        expected = {
            "MYSQL_DATABASE_NAME": "ciclops",
            "MYSQL_USER": "ciclops",
            "MYSQL_PASSWORD": "123",
            "MYSQL_HOST": "localhost",
            "MYSQL_PORT": "3306",
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])
        self.assertEqual("localhost", row[1])

        db = DatabaseManager("ciclops")
        db.drop_user()
        db.drop()

    def test_drop(self):
        db = DatabaseManager("ciclops")
        db.create()
        db.create_user()

        request = RequestFactory().delete("/ciclops")
        response = drop(request, "ciclops")
        self.assertEqual(200, response.status_code)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)


class DatabaseTestCase(TestCase):

    def setUp(self):
        self.cursor = connection.cursor()

    def test_create(self):
        db = DatabaseManager("newdatabase")
        db.create()
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'newdatabase'")
        row = self.cursor.fetchone()
        self.assertEqual("newdatabase", row[0])
        db.drop()

    def test_drop(self):
        db = DatabaseManager("otherdatabase")
        db.create()
        db.drop()
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'otherdatabase'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_create_user(self):
        db = DatabaseManager("wolverine")
        db.create_user()
        self.cursor.execute("select User, Host FROM mysql.user WHERE User='wolverine' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertEqual("wolverine", row[0])
        self.assertEqual("localhost", row[1])
        db.drop_user()

    def test_drop_user(self):
        db = DatabaseManager("magneto")
        db.create_user()
        db.drop_user()
        self.cursor.execute("select User, Host FROM mysql.user WHERE User='wolverine' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)