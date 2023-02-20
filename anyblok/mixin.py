# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.registry import RegistryManager


class MixinType:
    @classmethod
    def register(cls, parent, name, cls_, **kwargs):
        """add new sub registry in the registry

        :param parent: Existing global registry
        :param name: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """
        _registryname = parent.__registry_name__ + "." + name

        if not hasattr(parent, name):
            kwargs["__registry_name__"] = _registryname
            ns = type(name, tuple(), kwargs)
            setattr(parent, name, ns)

        if parent is Declarations:
            return  # pragma: no cover

        RegistryManager.add_entry_in_register(
            cls.__name__, _registryname, cls_, **kwargs
        )

    @classmethod
    def unregister(cls, entry, cls_):
        """Remove the Interface in the registry

        :param entry: entry declaration of the model where the ``cls_``
            must be removed
        :param cls_: Class Interface to remove in registry
        """
        RegistryManager.remove_in_register(cls_)


@Declarations.add_declaration_type(isAnEntry=True)
class Mixin(MixinType):
    """The Mixin class are used to define a behaviours on models:

    * Add new mixin class::

        @Declarations.register(Declarations.Mixin)
        class MyMixinclass:
            pass

    * Remove a mixin class::

        Declarations.unregister(Declarations.Mixin.MyMixinclass, MyMixinclass)
    """

    autodoc_anyblok_bases = True

    autodoc_anyblok_fields = True
