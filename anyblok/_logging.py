# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import logging
from syslog import LOG_USER
from functools import wraps
from anyblok.environment import EnvironmentManager
from .common import function_name


LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}

FORMATTER = '%(asctime)s %(levelname)s - %(database)s:%(name)s - %(message)s'

logger = logging.getLogger('')


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, _N, DEFAULT = range(10)
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"
COLOR_PATTERN = "%s%s%%s%s" % (COLOR_SEQ, COLOR_SEQ, RESET_SEQ)
LEVEL_COLOR_MAPPING = {
    logging.DEBUG: (BLUE, DEFAULT),
    logging.INFO: (GREEN, DEFAULT),
    logging.WARNING: (YELLOW, DEFAULT),
    logging.ERROR: (RED, DEFAULT),
    logging.CRITICAL: (WHITE, RED),
}


class Formatter(logging.Formatter):
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
            EnvironmentManager.get('dbname', 'No database'))

        return logging.Formatter.format(self, record)


def init_logger(level='info', mode='console',
                filename=None, socket=None, facility=LOG_USER):
    """ Init the logger output

    There are 5 levels of logging
    * debug
    * info (default)
    * warning
    * error
    * critical

    Example::

        from anyblok.log import init_logger
        init_logger(level='debug')

    A logger can log to:

    * console (default)::

        init_logger(mode='console')

    * file::

        init_logger(mode='file', filename='my.file.log')

    * socket::

        init_logger(mode='socket', socket=('localhost', 1000))

    * syslog:

        Example::

            # By socket
            init_logger(mode='syslog', socket('localhost', 514))
            # By UNIX socket
            init_logger(mode='syslog', socket='/dev/log')

        the syslog mode define logger facility:

            * LOG_AUTH
            * LOG_AUTHPRIV
            * LOG_CRON
            * LOG_DAEMON
            * LOG_FTP
            * LOG_KERN
            * LOG_LPR
            * LOG_MAIL
            * LOG_NEWS
            * LOG_SYSLOG
            * LOG_USER (default)
            * LOG_UUCP
            * LOG_LOCAL0
            * LOG_LOCAL1
            * LOG_LOCAL2
            * LOG_LOCAL3
            * LOG_LOCAL4
            * LOG_LOCAL5
            * LOG_LOCAL6
            * LOG_LOCAL7

        example::

            init_logger(mode='syslog', socket='/dev/log',
                        facility=syslog.LOG_SYSLOG)

    :param level: level defined by anyblok
    :param mode: Output mode
    :param filename: Output file
    :param socket: Socket or UnixSocket
    :param facility:
    :exception: Exception
    """
    if logger.hasHandlers():
        for h in logger.handlers:
            if h.get_name() == mode:
                return

    level = LEVELS.get(level, logging.INFO)

    logger.setLevel(level)

    Formatter_fnct = logging.Formatter

    if mode == 'console':
        handler = logging.StreamHandler()
        Formatter_fnct = Formatter
    elif mode == 'file' and filename:
        handler = logging.handlers.RotatingFileHandler(filename)
    elif mode == 'socket' and socket:
        if not isinstance(socket, (list, tuple)):
            raise Exception("Invalid argument, socket must be a list or "
                            "tuple (host, port)")
        handler = logging.handlers.SocketHandler(*socket)
    elif mode == 'syslog' and socket:
        handler = logging.handlers.SysLogHandler(
            address=socket, facility=facility)
    else:
        raise Exception("Invalid mode")

    handler.setLevel(level)

    formatter = Formatter_fnct(fmt=FORMATTER, datefmt='%Y-%m%d %H:%M:%S')
    handler.setFormatter(formatter)
    handler.set_name(mode)
    logger.addHandler(handler)


def log(level='info', withargs=False):
    """ decorator to log the entry of a method

    There are 5 levels of logging
    * debug
    * info (default)
    * warning
    * error
    * critical

    example::

        @log()
        def foo(...):
            ...

    :param level: AnyBlok log level
    :param withargs: If True, add args and kwargs in the log message
    """
    log = logger

    def wrapper(function):
        @wraps(function)
        def f(*args, **kwargs):
            if level == 'debug' or withargs:
                getattr(log, level)("%s with args %r and kwargs %r" % (
                    function_name(function), args, kwargs))
            else:
                getattr(log, level)(function_name(function))

            return function(*args, **kwargs)

        return f

    return wrapper
