# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import logging
from functools import wraps
from anyblok.environment import EnvironmentManager
from .common import function_name


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, _N, DEFAULT = range(10)
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
COLOR_PATTERN = "%s%s%%s%s" % (COLOR_SEQ, COLOR_SEQ, RESET_SEQ)
LEVEL_COLOR_MAPPING = {
    logging.DEBUG: (BLUE, DEFAULT),
    logging.INFO: (GREEN, DEFAULT),
    logging.WARNING: (YELLOW, DEFAULT),
    logging.ERROR: (RED, DEFAULT),
    logging.CRITICAL: (WHITE, RED),
}


class consoleFormatter(logging.Formatter):
    """ Define the format for console logging """

    def format(self, record):
        """ Add color to the message

        :param record: logging record instance
        :rtype: logging record formatted
        """
        fg_color, bg_color = LEVEL_COLOR_MAPPING[record.levelno]
        record.levelname = COLOR_PATTERN % (
            30 + fg_color, 40 + bg_color, record.levelname)
        fg_color, bg_color = CYAN, DEFAULT
        record.database = COLOR_PATTERN % (
            30 + fg_color, 40 + bg_color,
            EnvironmentManager.get('db_name', 'No database'))

        return logging.Formatter.format(self, record)


class anyblokFormatter(logging.Formatter):
    """ Define the format for console logging """

    def format(self, record):
        """ Add color to the message

        :param record: logging record instance
        :rtype: logging record formatted
        """
        record.database = EnvironmentManager.get('db_name', 'No database')
        return logging.Formatter.format(self, record)


def log(logger, level='info', withargs=False):
    """ decorator to log the entry of a method

    There are 5 levels of logging
    * debug
    * info (default)
    * warning
    * error
    * critical

    example::

        from logging import getLogger
        logger = getLogger(__name__)

        @log(logger)
        def foo(...):
            ...

    :param level: AnyBlok log level
    :param withargs: If True, add args and kwargs in the log message
    """

    def wrapper(function):
        @wraps(function)
        def f(*args, **kwargs):
            if level == 'debug' or withargs:
                getattr(logger, level)("%s with args %r and kwargs %r" % (
                    function_name(function), args, kwargs))
            else:
                getattr(logger, level)(function_name(function))

            return function(*args, **kwargs)

        return f

    return wrapper
