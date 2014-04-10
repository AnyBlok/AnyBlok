from sqlalchemy.types import DECIMAL as SA_Decimal
from AnyBlok import target_registry, Column


@target_registry(Column)
class Decimal(Column):
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
