from sqlalchemy.types import Time as SA_Time
from AnyBlok import target_registry, Column


@target_registry(Column)
class Time(Column):
    """ Time column

    ::

        from datetime import time
        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Time

        @target_registry(Model)
        class Test:

            x = Time(label="Time", default=time())

    """
    sqlalchemy_type = SA_Time
