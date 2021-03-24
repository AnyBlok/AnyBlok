# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy import event


def mysql_no_autocommit(engine):

    def mysql_set_no_autocommit(dbapi_con, connection_record):
        cur = dbapi_con.cursor()
        cur.execute("SET autocommit=0;")
        cur.execute("SET SESSION sql_mode='TRADITIONAL';")
        cur = None

    event.listen(engine, 'connect', mysql_set_no_autocommit)
