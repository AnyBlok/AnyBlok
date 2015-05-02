# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
import datetime
from json import loads


register = Declarations.register
IO = Declarations.Model.IO
LargeBinary = Declarations.Column.LargeBinary
Boolean = Declarations.Column.Boolean
Integer = Declarations.Column.Integer


@register(Declarations.Exception)
class FormaterException(Exception):
    """Simple Exception for importer"""


@register(IO)
class Formater:

    def str2value(self, value, model):
        return value

    def _externalIdStr2value(self, value, model):
        mapping = self.registry.IO.Mapping.get(model, value)
        if mapping is None:
            raise Declarations.Exception.FormaterException(
                "Unexisting maping key %r with model %r" % (value, model))

        return mapping

    def externalIdStr2value(self, value, model):
        entry = self._externalIdStr2value(value, model)
        pks = entry.to_primary_keys()
        if len(pks.keys()) > 1:
            raise Declarations.Exception.FormaterException(
                "Foreign key on multi primary keys does not implemented yet")

        return [x for x in pks.values()][0]


@register(IO.Formater)
class Float(IO.Formater):

    def str2value(self, value, model):
        return float(value)


@register(IO.Formater)
class Decimal(IO.Formater):

    def str2value(self, value, model):
        from decimal import Decimal as D
        return D(value)


@register(IO.Formater)
class Json(IO.Formater):

    def str2value(self, value, model):
        return loads(value)


@register(IO.Formater)
class Interval(IO.Formater):

    def str2value(self, value, model):
        return datetime.timedelta(seconds=int(value))


@register(IO.Formater)
class Integer(IO.Formater):

    def str2value(self, value, model):
        return int(value)


@register(IO.Formater)
class SmallInteger(IO.Formater.Integer):
    pass


@register(IO.Formater)
class BigInteger(IO.Formater.Integer):
    pass


@register(IO.Formater)
class Boolean(IO.Formater):

    def str2value(self, value, model):
        if value in ("1", "true", "True", 1, True):
            return True
        elif value in ("0", "false", "False", '', 0, False):
            return False

        raise Declarations.Exception.FormaterException(
            "Value %r is not a boolean" % value)


@register(IO.Formater)
class Time(IO.Formater):

    def str2value(self, value, model):
        dt = datetime.datetime.strptime(value, "%H:%M:%S")
        return datetime.time(dt.hour, dt.minute, dt.second)


@register(IO.Formater)
class Date(IO.Formater):

    def str2value(self, value, model):
        dt = datetime.datetime.strptime(value, "%Y-%m-%d")
        return datetime.date(dt.year, dt.month, dt.day)


@register(IO.Formater)
class DateTime(IO.Formater):

    def str2value(self, value, model):
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
