# -*- coding: utf-8 -*-
import unittest
import os
from anyblok import ArgsParseManager, AnyBlok
from zope.component import getUtility
from datetime import datetime


class TestDataBase(unittest.TestCase):

    drivername = None
    ready_to_test = False

    def setUp(self):
        super(TestDataBase, self).setUp()
        self.load_env_for_drivername()

    def load_env_for_drivername(self):

        if self.drivername is None:
            return

        env = os.environ
        if not bool(env.get(self.drivername)):
            return

        env = {
            'dbname': env.get(self.drivername + '_dbname', 'anyblok'),
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
        adapter = getUtility(
            AnyBlok.Interface.ISqlAlchemyDataBase, self.drivername)

        adapter.createdb(dbname)
        has_dblist = dbname in adapter.listdb()
        self.assertEqual(has_dblist, True)

        adapter.dropdb(dbname)
        has_dblist = dbname in adapter.listdb()
        self.assertEqual(has_dblist, False)
