from sqlalchemy.types import Date as SA_Date
from AnyBlok import target_registry, Column


@target_registry(Column)
class Date(Column):

        sqlalchemy_type = SA_Date
