# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from sqlalchemy.ext.hybrid import hybrid_property


@Declarations.register(Declarations.Field)
class Function(Declarations.Field):
    """ Function Field

    ::

        from AnyBlok.declarations import Declarations


        register = Declarations.register
        Model = Declarations.Model
        Function = Declarations.Field.Function

        @register(Model)
        class Test:
            x = Function(fget='fget', fset='fset', fdel='fdel', fexp='fexpr')

    """

    def update_properties(self, registry, namespace, fieldname, properties):

        def wrap(method, ormethod=None):
            m = self.kwargs.get(method)
            if m is None:
                if ormethod:
                    m = self.kwargs.get(method)
                    if m is None:
                        return None

            def function_method(model_self, *args, **kwargs):
                if method == 'fexpr':
                    return getattr(model_self, m)(model_self, *args, **kwargs)
                elif method == 'fget':
                    loaded_namespaces = model_self.registry.loaded_namespaces
                    registry_name = model_self.__registry_name__
                    if model_self is loaded_namespaces[registry_name]:
                        return getattr(model_self, m)(model_self, *args,
                                                      **kwargs)
                    else:
                        return getattr(model_self, m)(*args, **kwargs)
                else:
                    return getattr(model_self, m)(*args, **kwargs)

            return function_method

        fget = wrap('fget')
        fset = wrap('fset')
        fdel = wrap('fdel')
        fexpr = wrap('fexpr', 'fget')

        self.format_label(fieldname)
        properties['loaded_fields'][fieldname] = self.label
        properties[fieldname] = hybrid_property(
            fget, fset, fdel=fdel, expr=fexpr)
