from sqlalchemy.types import Time as SA_Time
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Time(Declarations.Column):
    """ Time column

    ::

        from datetime import time
        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Time = Declarations.Time

        @target_registry(Model)
        class Test:

            x = Time(default=time())

    """
    sqlalchemy_type = SA_Time
