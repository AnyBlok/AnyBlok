from sqlalchemy.types import Boolean as SA_Boolean
from AnyBlok import target_registry, Column


@target_registry(Column)
class Boolean(Column):

        sqlalchemy_type = SA_Boolean
