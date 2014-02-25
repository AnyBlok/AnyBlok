from sqlalchemy.types import DateTime as SA_DateTime
from AnyBlok import target_registry, Column


@target_registry(Column)
class DateTime(Column):

        sqlalchemy_type = SA_DateTime
