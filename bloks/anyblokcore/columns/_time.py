from sqlalchemy.types import Time as SA_Time
from AnyBlok import target_registry, Column


@target_registry(Column)
class Time(Column):

        sqlalchemy_type = SA_Time
