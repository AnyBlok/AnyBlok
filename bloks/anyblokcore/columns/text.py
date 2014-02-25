from sqlalchemy.types import Text as SA_Text
from AnyBlok import target_registry, Column


@target_registry(Column)
class Text(Column):

        sqlalchemy_type = SA_Text
