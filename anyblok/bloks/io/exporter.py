# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from .exceptions import ExporterException


@Declarations.register(Declarations.Model.IO)
class Exporter(Declarations.Mixin.IOMixin):

    def run(self, entries):
        for entry in entries:
            if entry.__registry_name__ != self.model:
                raise ExporterException(
                    "The entries must be instance of %r" % self.model)

        return self.get_model(self.mode)(self).run(entries)

    @classmethod
    def get_external_id(cls, model):
        Sequence = cls.registry.System.Sequence
        seq_code = 'export.%s' % model
        query = Sequence.query().filter(Sequence.code == seq_code)
        if query.count():
            sequence = query.first()
        else:
            sequence = Sequence.insert(formater="{code}_{seq}", code=seq_code)

        return sequence.nextval()

    @classmethod
    def get_key_mapping(cls, entry):
        Mapping = cls.registry.IO.Mapping
        mapping = Mapping.get_from_entry(entry)
        if mapping:
            return mapping.key

        key = cls.get_external_id(entry.__registry_name__)
        Mapping.set(key, entry)
        return key

    def value2str(self, value, ctype, external_id=False, model=None):
        formater = self.get_formater(ctype)
        if external_id:
            return formater.externalIdValue2str(value, model)

        return formater.value2str(value, model)
