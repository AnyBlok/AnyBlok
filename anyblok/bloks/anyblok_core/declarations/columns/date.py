from sqlalchemy.types import Date as SA_Date
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Date(Declarations.Column):
    """ DataTime column

    ::

        from datetime import date
        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Date = Declarations.Column.Date

        @target_registry(Model)
        class Test:

            x = Date(default=date.today())

    """
    sqlalchemy_type = SA_Date
