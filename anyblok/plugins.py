# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2019 Joachim Trouverie
#    Copyright (C) 2020 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy.dialects.mysql.types import TINYINT
from sqlalchemy.dialects.mssql.base import BIT
from sqlalchemy.sql.sqltypes import Boolean, DateTime
from logging import getLogger
from .migration import MigrationColumnTypePlugin
logger = getLogger(__name__)


class BooleanToTinyIntMySQL(MigrationColumnTypePlugin):

    to_type = Boolean
    from_type = TINYINT
    dialect = ['MySQL', 'MariaDB']

    def need_to_modify_type(self):
        '''Boolean are TINYINT in MySQL DataBases'''
        return False

    def apply(self, column, **kwargs):
        '''Boolean are TINYINT in MySQL DataBases'''
        # do nothing
        pass  # pragma: no cover


class DateTimeToDateTimeMySQL(MigrationColumnTypePlugin):

    to_type = DateTime
    from_type = DateTime
    dialect = ['MySQL', 'MariaDB']

    def need_to_modify_type(self):
        return False

    def apply(self, column, **kwargs):
        pass  # pragma: no cover


class BooleanToBitMsSQL(MigrationColumnTypePlugin):

    to_type = Boolean
    from_type = BIT
    dialect = ['MsSQL']

    def need_to_modify_type(self):
        '''Boolean are Bit in MsSQL DataBases'''
        return False

    def apply(self, column, **kwargs):
        '''Boolean are Bit in MsSQL DataBases'''
        # do nothing
        pass  # pragma: no cover
