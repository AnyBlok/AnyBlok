# -*- coding: utf-8 -*-
from anyblok.tests.testcase import TestCase
from anyblok.databases.interface import ISqlAlchemyDataBaseType
import os
from anyblok._argsparse import ArgsParseManager
from zope.component import getUtility
from datetime import datetime


class TestDataBase(TestCase):

    drivername = None
    ready_to_test = False

    def setUp(self):
        super(TestDataBase, self).setUp()
        self.load_env_for_drivername()

    def load_env_for_drivername(self):

        if self.drivername is None:
            return

        env = os.environ

        env = {
            'dbname': env.get(self.drivername + '_dbname', 'test_db_anyblok'),
            'dbdrivername': self.drivername,
            'dbusername': env.get(self.drivername + '_dbusername'),
            'dbpassword': env.get(self.drivername + '_dbpassword'),
            'dbhost': env.get(self.drivername + '_dbhost', 'localhost'),
            'dbport': env.get(self.drivername + '_dbport'),
        }
        ArgsParseManager.configuration = env
        self.ready_to_test = True


class TestPostgres(TestDataBase):

    drivername = 'postgres'

    def test_database(self):
        if not self.ready_to_test:
            return

        dbname = ArgsParseManager.get('dbname') + datetime.strftime(
            datetime.today(), '%Y-%m-%d_%H:%M:%S')
        adapter = getUtility(ISqlAlchemyDataBaseType, self.drivername)

        adapter.createdb(dbname)
        has_dblist = dbname in adapter.listdb()
        self.assertEqual(has_dblist, True)

        adapter.dropdb(dbname)
        has_dblist = dbname in adapter.listdb()
        self.assertEqual(has_dblist, False)
