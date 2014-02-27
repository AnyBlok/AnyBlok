from sqlalchemy.types import Enum as SA_Enum
from AnyBlok import target_registry, Column


@target_registry(Column)
class Enum(Column):

        sqlalchemy_type = SA_Enum
