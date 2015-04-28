# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations


@Declarations.register(Declarations.Model.IO)
class Exporter(Declarations.Mixin.IOMixin):

    def run(self, entries):
        return self.get_model(self.mode)(self).run(entries)

    @classmethod
    def get_counter(cls, model):
        Sequence = cls.registry.System.Sequence
        seq_code = 'export.%s' % model
        query = Sequence.query().filter(Sequence.code == seq_code)
        if query.count():
            sequence = query.first()
        else:
            sequence = Sequence.insert(code=seq_code, prefix=seq_code)

        return sequence.nextval()

    @classmethod
    def get_key_maping(cls, entry):
        Mapping = cls.registry.IO.Mapping
        model = entry.__registry_name__
        mapping = Mapping.get_from_model_and_pyramid_keys(
            model, entry.to_primary_keys())
        if mapping:
            return mapping.key

        key = cls.get_counter(model)
        Mapping.set(key, entry)
        return key
