from sqlalchemy.types import Float as SA_Float
from AnyBlok import target_registry, Column


@target_registry(Column)
class Float(Column):

    sqlalchemy_type = SA_Float
