# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import sys


def function_name(function):
    if sys.version_info < (3, 3):
        return function.__name__
    else:
        return function.__qualname__


def python_version():
    vi = sys.version_info
    return (vi.major, vi.minor)
