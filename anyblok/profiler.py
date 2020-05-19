# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2020 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import cProfile
import pstats
import io
from contextlib import contextmanager
from pstats import SortKey
from logging import getLogger


logger = getLogger(__name__)


class Profiler:

    def __init__(self, filename=None):
        self.pr = cProfile.Profile()
        self.filename = filename

    def enable(self):
        logger.info('Enable the profiler')
        self.pr.enable()

    def disable(self):
        logger.info('Disable the profiler')
        self.pr.disable()

    def __call__(self, fn):
        def wrapper(*a, **kw):
            with self.listen():
                return fn(*a, **kw)

        return wrapper

    @contextmanager
    def listen(self):
        self.enable()
        try:
            yield
        finally:
            self.disable()

    def __enter__(self):
        self.enable()
        return

    def __exit__(self, type, value, traceback):
        self.disable()
        self.print_stats()
        return True

    def print_stats(self):
        from .config import Configuration

        if self.filename:
            filename = self.filename
        else:
            filename = Configuration.get(
                'profiler_filename', 'anyblok_profiler.txt')

        logger.info('Save the profile in %s', filename)
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(self.pr, stream=s).sort_stats(sortby)
        ps.dump_stats(filename)
        if Configuration.get('print_profiler', True):
            ps.print_stats()
            print(s.getvalue())


def quick_profiler(filename):
    def wrapper_fn(fn):
        def wrapper_call(*a, **kw):
            profiler = Profiler(filename=filename)
            with profiler.listen():
                res = fn(*a, **kw)

            profiler.print_stats()
            return res

        return wrapper_call
    return wrapper_fn
