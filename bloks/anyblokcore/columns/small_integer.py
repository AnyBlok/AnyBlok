from sqlalchemy.types import SmallInteger as SA_SmallInteger
from AnyBlok import target_registry, Column


@target_registry(Column)
class SmallInteger(Column):

    sqlalchemy_type = SA_SmallInteger
