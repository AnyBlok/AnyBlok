# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
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
class Integer(IO.Importer.Field):

    def field_value(self, value):
        return int(value)

    def field_external_id(self, value, model):
        return int(super(Integer, self).field_external_id(value, model))

# TODO Add other field
