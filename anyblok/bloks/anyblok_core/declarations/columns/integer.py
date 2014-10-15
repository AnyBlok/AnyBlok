from sqlalchemy.types import Integer as SA_Integer
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Integer(Declarations.Column):
    """ Integer column

    ::

        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Integer = Declarations.Integer

        @target_registry(Model)
        class Test:

            x = Integer(default=1)

    """
    sqlalchemy_type = SA_Integer
