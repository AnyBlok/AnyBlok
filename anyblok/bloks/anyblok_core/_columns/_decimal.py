from sqlalchemy.types import DECIMAL as SA_Decimal
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Decimal(Declarations.Column):
    """ Decimal column

    ::

        from dedimal import Decimal as D
        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Decimal

        @target_registry(Model)
        class Test:

            x = Decimal(label="Decimal", default=D('1.1'))

    """
    sqlalchemy_type = SA_Decimal
