from sqlalchemy.types import Time as SA_Time
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Time(Declarations.Column):
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
