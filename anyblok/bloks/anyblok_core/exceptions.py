# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.


class CoreBaseException(TypeError):
    """ Exception for ``Core.Base`` """


class SqlBaseException(Exception):
    """ Simple Exception for sql base """


class QueryException(Exception):
    """ Simple Exception for query """


class CacheException(Exception):
    """ Simple Exception for the cache Model """


class ParameterException(Exception):
    """ Simple exception for System.Parameter """


class CronWorkerException(Exception):
    """ Simple exception for System.Parameter """
