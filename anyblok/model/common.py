# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .factory import has_sql_fields  # noqa
from .factory import ModelFactory, ViewFactory, ModelFactoryException
import warnings

MODEL = 'MODEL'
VIEW = 'VIEW'


def get_factory(type_):
    warnings.warn(
        "type attribute is deprecated to define a type"
        " of model, you have to use the factory",
        DeprecationWarning, stacklevel=2)
    if type_ == MODEL:
        return ModelFactory
    elif type_ == VIEW:
        return ViewFactory
    else:
        raise ModelFactoryException("The type %r is unknown" % type_)
