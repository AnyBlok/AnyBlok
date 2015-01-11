# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
import os
from anyblok._argsparse import ArgsParseManager
from datetime import datetime
import anyblok


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
            'dbhost': env.get(self.drivername + '_dbhost'),
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
        bdd = anyblok.BDD[self.drivername]
        bdd.createdb(dbname)
        has_dblist = dbname in bdd.listdb()
        self.assertEqual(has_dblist, True)

        bdd.dropdb(dbname)
        has_dblist = dbname in bdd.listdb()
        self.assertEqual(has_dblist, False)
