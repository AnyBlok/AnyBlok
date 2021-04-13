# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.registry import RegistryManager
from anyblok import Declarations


@Declarations.add_declaration_type()
class Core:
    """ The Core class is the base of all the AnyBlok models

    Add new core model::

        @Declarations.register(Declarations.Core)
        class Base:
            pass

    Remove the core model::

        Declarations.unregister(Declarations.Core, 'Base', Base,
                                     blok='MyBlok')

    """

    @classmethod
    def register(self, parent, name, cls_, **kwargs):
        """ Add new sub registry in the registry

        :param parent: Existing declaration
        :param name: Name of the new declaration to add it
        :param cls_: Class Interface to add in the declaration
        """
        if not hasattr(parent, name):
            core = type(name, tuple(), {})
            setattr(parent, name, core)

        if parent == Declarations:
            return  # pragma: no cover

        RegistryManager.add_core_in_register(name, cls_)

    @classmethod
    def unregister(self, entry, cls_):
        """ Remove the Interface from the registry

        :param entry: entry declaration of the model where the ``cls_``
            must be removed
        :param cls_: Class Interface to remove in the declaration
        """
        RegistryManager.remove_in_register(cls_)


RegistryManager.declare_core('Base')
RegistryManager.declare_core('SqlBase')
RegistryManager.declare_core('SqlViewBase')
RegistryManager.declare_core('Session')
RegistryManager.declare_core('Query')
RegistryManager.declare_core('InstrumentedList')
