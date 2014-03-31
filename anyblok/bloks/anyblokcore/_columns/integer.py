from sqlalchemy.types import Integer as SA_Integer
from AnyBlok import target_registry, Column


@target_registry(Column)
class Integer(Column):

    sqlalchemy_type = SA_Integer
