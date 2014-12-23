# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.registry import RegistryManager
from anyblok import Declarations


@Declarations.add_declaration_type(isAnEntry=True)
class Mixin:
    """ The Mixin class are used to define a behaviour on an one or more model:

    * Add new mixin class::

        @Declarations.target_registry(Declarations.Mixin)
        class MyMixinclass:
            pass

    * Remove a mixin class::

        Declarations.remove_registry(Declarations.Mixin, 'MyMixinclass',
                                     MyMixinclass, blok='MyBlok')
    """

    @classmethod
    def target_registry(self, parent, name, cls_, **kwargs):
        """ add new sub registry in the registry

        :param parent: Existing global registry
        :param name: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """
        _registryname = parent.__registry_name__ + '.' + name

        if not hasattr(parent, name):
            kwargs['__registry_name__'] = _registryname
            ns = type(name, tuple(), kwargs)
            setattr(parent, name, ns)

        if parent is Declarations:
            return

        RegistryManager.add_entry_in_target_registry(
            'Mixin', _registryname, cls_, **kwargs)

    @classmethod
    def remove_registry(self, entry, cls_):
        """ Remove the Interface in the registry

        :param entry: entry declaration of the model where the ``cls_``
            must be removed
        :param cls_: Class Interface to remove in registry
        """
        RegistryManager.remove_in_target_registry(cls_)
