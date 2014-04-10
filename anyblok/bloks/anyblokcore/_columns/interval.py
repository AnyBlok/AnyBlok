from sqlalchemy.types import Interval as SA_Interval
from AnyBlok import target_registry, Column


@target_registry(Column)
class Interval(Column):
    """ Data time interval column

    ::

        from datetime import timedelta
        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Interval

        @target_registry(Model)
        class Test:

            x = Interval(label="Interval", default=timedelta(days=5))

    """
    sqlalchemy_type = SA_Interval
