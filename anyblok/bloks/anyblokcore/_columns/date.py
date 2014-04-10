from sqlalchemy.types import Date as SA_Date
from AnyBlok import target_registry, Column


@target_registry(Column)
class Date(Column):
    """ DataTime column

    ::

        from datetime import date
        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Date

        @target_registry(Model)
        class Test:

            x = Date(label="Date", default=date.today())

    """
    sqlalchemy_type = SA_Date
