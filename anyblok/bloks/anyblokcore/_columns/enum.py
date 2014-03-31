from sqlalchemy.types import Enum as SA_Enum
from AnyBlok import target_registry, Column


@target_registry(Column)
class Enum(Column):

        def __init__(self, *args, **kwargs):
            self.sqlalchemy_type = SA_Enum(*args)
            super(Enum, self).__init__(**kwargs)
