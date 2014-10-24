from anyblok import Declarations
from sqlalchemy.ext.hybrid import hybrid_property


@Declarations.target_registry(Declarations.Field)
class Function(Declarations.Field):
    """ Function Field

    ::

        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Function = Declarations.Field.Function

        @target_registry(Model)
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
