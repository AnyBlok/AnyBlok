from sqlalchemy.types import Boolean as SA_Boolean
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Boolean(Declarations.Column):
    """ Boolean column

    ::

        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Boolean = Declarations.Column.Boolean

        @target_registry(Model)
        class Test:

            x = Boolean(default=True)

    """
    sqlalchemy_type = SA_Boolean
