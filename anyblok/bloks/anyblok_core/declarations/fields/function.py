from anyblok import Declarations
from sqlalchemy.ext.hybrid import hybrid_property


@Declarations.target_registry(Declarations.Field)
class Function(Declarations.Field):

    def update_properties(self, registry, namespace, fieldname, properties):

        def wrap(method):
            m = self.kwargs.get(method)
            if m is None:
                return None

            def function_method(model_self, *args, **kwargs):
                if method == 'fexpr':
                    return getattr(model_self, m)(model_self, *args, **kwargs)
                else:
                    return getattr(model_self, m)(*args, **kwargs)

            return function_method

        fget = wrap('fget')
        fset = wrap('fset')
        fdel = wrap('fdel')
        fexpr = wrap('fexpr')

        properties['loaded_columns'].remove(fieldname)
        properties[fieldname] = hybrid_property(
            fget, fset, fdel=fdel, expr=fexpr)
