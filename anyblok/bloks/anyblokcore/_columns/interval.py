from sqlalchemy.types import Interval as SA_Interval
from AnyBlok import target_registry, Column


@target_registry(Column)
class Interval(Column):

        sqlalchemy_type = SA_Interval
