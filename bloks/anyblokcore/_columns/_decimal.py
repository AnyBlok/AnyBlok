from sqlalchemy.types import DECIMAL as SA_Decimal
from AnyBlok import target_registry, Column


@target_registry(Column)
class Decimal(Column):

        sqlalchemy_type = SA_Decimal
