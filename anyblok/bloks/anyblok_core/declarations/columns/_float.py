from sqlalchemy.types import Float as SA_Float
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Float(Declarations.Column):
    """ Float column

    ::

        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Float = Declarations.Column.Float

        @target_registry(Model)
        class Test:

            x = Float(default=1.0)

    """
    sqlalchemy_type = SA_Float
