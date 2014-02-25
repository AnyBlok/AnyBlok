from sqlalchemy.types import LargeBinary as SA_LargeBinary
from AnyBlok import target_registry, Column


@target_registry(Column)
class LargeBinary(Column):

        sqlalchemy_type = SA_LargeBinary
