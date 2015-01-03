# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from .declarations import DeclarationsException
from anyblok.environment import EnvironmentManager, EnvironmentException


@Declarations.add_declaration_type()
class Exception:
    """ Adapter to Exception Class

    The Exception class is used to define the type of Declarations Exception

    Add new Exception type::

        @Declarations.target_registry(Declarations.Exception)
        class MyException:
            pass

    Removing the exception is forbidden because it can be used
    """

    @classmethod
    def target_registry(self, parent, name, cls_, **kwargs):
        """ add new sub registry in the registry

        :param parent: Existing declaration
        :param name: Name of the new declaration to add it
        :param cls_: Class to add in the declaration
        :exception: DeclarationsException
        """
        _registryname = parent.__registry_name__ + '.' + name
        if hasattr(parent, name) and not EnvironmentManager.get('reload',
                                                                False):
            raise DeclarationsException(
                "The Exception %r already exist" % _registryname)

        setattr(cls_, '__registry_name__', _registryname)
        setattr(cls_, '__declaration_type__', parent.__declaration_type__)
        setattr(parent, name, cls_)

    @classmethod
    def remove_registry(self, entry, cls_):
        """ Forbidden method

        :exception: DeclarationsException
        """
        raise DeclarationsException("Removing an exception is forbidden")


Declarations.target_registry(Declarations.Exception,
                             cls_=DeclarationsException)
Declarations.target_registry(Declarations.Exception,
                             cls_=EnvironmentException)
