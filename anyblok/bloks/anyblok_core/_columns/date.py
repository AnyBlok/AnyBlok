from sqlalchemy.types import Date as SA_Date
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Date(Declarations.Column):
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
