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
class ImporterException(Exception):
    """Simple Exception for importer"""


@register(IO)
class Importer(Declarations.Mixin.IOMixin):

    file_to_import = LargeBinary(nullable=False)
    offset = Integer(default=0)
    nb_grouped_lines = Integer(nullable=False, default=50)
    commit_at_each_grouped = Boolean(default=True)
    check_import = Boolean(default=False)

    def run(self):
        return self.get_model(self.mode)(self).run()

    def get_key_mapping(self, key):
        Mapping = self.registry.IO.Mapping
        return Mapping.get(self.model, key)

    def commit(self):
        if self.check_import:
            return False
        elif not self.commit_at_each_grouped:
            return False

        self.registry.commit()
        return True

    def format_field_value(self, value, ctype, external_id=False, model=None):
        if self.registry.has('Model.IO.Importer.' + ctype):
            formater = self.registry.get('Model.IO.Importer.' + ctype)()
        else:
            formater = self.registry.IO.Importer.Field()

        if external_id:
            return formater.field_external_id(value, model)
        return formater.field_value(value)


@register(IO.Importer)
class Field:

    def field_value(self, value):
        return value

    def _field_external_id(self, value, model):
        mapping = self.registry.IO.Mapping.get(model, value)
        if mapping is None:
            raise Declarations.Exception.ImporterException(
                "Unexisting maping key %r with model %r" % (value, model))

        return mapping

    def field_external_id(self, value, model):
        entry = self._field_external_id(value, model)
        pks = entry.to_primary_keys()
        if len(pks.keys()) > 1:
            raise Declarations.Exception.ImporterException(
                "Foreign key on multi primary keys does not implemented yet")

        return [x for x in pks.values()][0]


@register(IO.Importer)
class Float(IO.Importer.Field):

    def field_value(self, value):
        return float(value)


@register(IO.Importer)
class Decimal(IO.Importer.Field):

    def field_value(self, value):
        from decimal import Decimal as D
        return D(value)


@register(IO.Importer)
class Json(IO.Importer.Field):

    def field_value(self, value):
        return loads(value)


@register(IO.Importer)
class Interval(IO.Importer.Field):

    def field_value(self, value):
        return datetime.timedelta(seconds=int(value))


@register(IO.Importer)
class Integer(IO.Importer.Field):

    def field_value(self, value):
        return int(value)


@register(IO.Importer)
class SmallInteger(IO.Importer.Integer):
    pass


@register(IO.Importer)
class BigInteger(IO.Importer.Integer):
    pass


@register(IO.Importer)
class Boolean(IO.Importer.Field):

    def field_value(self, value):
        if value in ("1", "true", "True"):
            return True
        elif value in ("0", "false", "False"):
            return False

        raise Declarations.Exception.ImporterException(
            "Value %r is not a boolean" % value)


@register(IO.Importer)
class Time(IO.Importer.Field):

    def field_value(self, value):
        dt = datetime.datetime.strptime(value, "%H:%M:%S")
        return datetime.time(dt.hour, dt.minute, dt.second)


@register(IO.Importer)
class Date(IO.Importer.Field):

    def field_value(self, value):
        dt = datetime.datetime.strptime(value, "%Y-%m-%d")
        return datetime.date(dt.year, dt.month, dt.day)


@register(IO.Importer)
class DateTime(IO.Importer.Field):

    def field_value(self, value):
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
