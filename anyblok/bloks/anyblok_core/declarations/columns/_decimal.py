from sqlalchemy.types import DECIMAL as SA_Decimal
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Decimal(Declarations.Column):
    """ Decimal column

    ::

        from dedimal import Decimal as D
        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Decimal = Declarations.Column.Decimal

        @target_registry(Model)
        class Test:

            x = Decimal(default=D('1.1'))

    """
    sqlalchemy_type = SA_Decimal
