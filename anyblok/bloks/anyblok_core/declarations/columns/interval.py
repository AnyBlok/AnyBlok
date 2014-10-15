from sqlalchemy.types import Interval as SA_Interval
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Interval(Declarations.Column):
    """ Data time interval column

    ::

        from datetime import timedelta
        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Interval = Declarations.Interval

        @target_registry(Model)
        class Test:

            x = Interval(default=timedelta(days=5))

    """
    sqlalchemy_type = SA_Interval
