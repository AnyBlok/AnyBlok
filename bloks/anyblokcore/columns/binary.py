from sqlalchemy.types import BINARY as SA_BINARY
from AnyBlok import target_registry, Column


@target_registry(Column)
class Binary(Column):

        sqlalchemy_type = SA_BINARY
