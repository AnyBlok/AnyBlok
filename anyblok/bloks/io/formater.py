# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
import datetime
from json import loads, dumps
from .exceptions import FormaterException


register = Declarations.register
IO = Declarations.Model.IO


@register(IO)
class Formater:

    def str2value(self, value, model):
        return value

    def _externalIdStr2value(self, value, model):
        mapping = self.registry.IO.Mapping.get(model, value)
        if mapping is None:
            raise FormaterException(
                "Unexisting maping key %r with model %r" % (value, model))

        return mapping

    def externalIdStr2value(self, value, model):
        entry = self._externalIdStr2value(value, model)
        pks = entry.to_primary_keys()
        if len(pks.keys()) > 1:
            raise FormaterException(
                "Foreign key on multi primary keys does not implemented yet")

        return [x for x in pks.values()][0]

    def value2str(self, value, model):
        if value is None:
            return ''

        return str(value)

    def externalIdValue2str(self, value, model):
        Model = self.registry.get(model)
        Mapping = self.registry.IO.Mapping
        pks = Model.get_primary_keys()
        if len(pks) > 1:
            raise FormaterException(
                "Foreign key on multi primary keys does not implemented yet")

        pks = {x: value for x in pks}
        mapping = Mapping.get_from_model_and_primary_keys(model, pks)

        if mapping is None:
            entry = Model.from_primary_keys(**pks)
            key = self.registry.IO.Exporter.get_external_id(model)
            Mapping.set(key, entry)
            return key

        return mapping.key


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

    def value2str(self, value, model):
        return dumps(value)


@register(IO.Formater)
class Interval(IO.Formater):

    def str2value(self, value, model):
        return datetime.timedelta(seconds=int(value))

    def value2str(self, value, model):
        return str(value.seconds)


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

        raise FormaterException(
            "Value %r is not a boolean" % value)

    def value2str(self, value, model):
        return '1' if value else '0'


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


@register(IO.Formater)
class Many2One(IO.Formater):

    def str2value(self, value, model):
        Model = self.registry.get(model)
        if not value:
            return None

        pks = loads(value)
        if not pks:
            return None

        if not isinstance(pks, dict):
            raise FormaterException(
                "Value %r for %r must be dict" % (
                    value, self.__registry_name__))

        return Model.from_primary_keys(**pks)

    def externalIdStr2value(self, value, model):
        return self._externalIdStr2value(value, model)

    def value2str(self, value, model):
        if value is None:
            return ''

        return dumps(value.to_primary_keys())

    def externalIdValue2str(self, value, model):
        if value is None:
            return ''

        Exporter = self.registry.IO.Exporter
        return Exporter.get_key_mapping(value)


@register(IO.Formater)
class One2One(IO.Formater.Many2One):
    pass


@register(IO.Formater)
class Many2Many(IO.Formater):

    def str2value(self, value, model):
        Model = self.registry.get(model)
        if not value:
            return None

        pks = loads(value)

        if not all(isinstance(x, dict) for x in pks):
            raise FormaterException(
                "All values in %r for %r must be dict" % (
                    value, self.__registry_name__))

        return [Model.from_primary_keys(**x) for x in pks if x]

    def externalIdStr2value(self, values, model):
        if not values:
            return None
        values = loads(values)
        return [self._externalIdStr2value(value, model) for value in values]

    def value2str(self, values, model):
        if not values:
            return dumps([])

        return dumps([value.to_primary_keys() for value in values])

    def externalIdValue2str(self, values, model):
        if not values:
            return dumps([])

        Exporter = self.registry.IO.Exporter
        return dumps([Exporter.get_key_mapping(value) for value in values])


@register(IO.Formater)
class One2Many(IO.Formater.Many2Many):
    pass
