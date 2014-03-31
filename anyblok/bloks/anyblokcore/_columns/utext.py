from sqlalchemy.types import UnicodeText
from AnyBlok import target_registry, Column


@target_registry(Column)
class uText(Column):

        sqlalchemy_type = UnicodeText
