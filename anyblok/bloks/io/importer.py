# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.column import LargeBinary, Boolean, Integer


@Declarations.register(Declarations.Model.IO)
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

    def str2value(self, value, ctype, external_id=False, model=None):
        formater = self.get_formater(ctype)
        if external_id:
            return formater.externalIdStr2value(value, model)

        return formater.str2value(value, model)
