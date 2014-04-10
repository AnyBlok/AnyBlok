from sqlalchemy.types import DateTime as SA_DateTime
from AnyBlok import target_registry, Column


@target_registry(Column)
class DateTime(Column):
    """ DataTime column

    ::

        from datetime import datetime
        from AnyBlok import target_registry, Model
        from AnyBlok.Column import DateTime

        @target_registry(Model)
        class Test:

            x = DateTime(label="Date time", default=datetime.now())

    """
    sqlalchemy_type = SA_DateTime
