# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations


@Declarations.register(Declarations.Core)
class Query:

    def delete(self, *args, **kwargs):
        """Inherit the Query.delete methods.::

            Model.query().delete(remove_mapping=True)

        :param remove_mapping: boolean, if check (default) the mapping is
            removed
        """
        remove_mapping = kwargs.pop('remove_mapping', True)
        if remove_mapping:
            Mapping = self.registry.IO.Mapping
            mappings = []
            for entry in self.all():
                mapping = Mapping.get_from_model_and_primary_keys(
                    entry.__registry_name__, entry.to_primary_keys())
                if mapping and mapping not in mappings:
                    mappings.append(mapping)

            res = super(Query, self).delete(*args, **kwargs)
            for mapping in mappings:
                Mapping.delete(mapping.model, mapping.key)

            return res

        return super(Query, self).delete(*args, **kwargs)


@Declarations.register(Declarations.Core)
class SqlBase:

    def delete(self, *args, **kwargs):
        """Inherit the Model.delete methods.::

            instance.delete(remove_mapping=True)

        :param remove_mapping: boolean, if check (default) the mapping is
            removed
        """
        remove_mapping = kwargs.pop('remove_mapping', True)
        if remove_mapping:
            Mapping = self.registry.IO.Mapping
            mapping = Mapping.get_from_model_and_primary_keys(
                self.__registry_name__, self.to_primary_keys())

            res = super(SqlBase, self).delete(*args, **kwargs)
            if mapping:
                Mapping.delete(mapping.model, mapping.key)

            return res

        return super(SqlBase, self).delete(*args, **kwargs)
