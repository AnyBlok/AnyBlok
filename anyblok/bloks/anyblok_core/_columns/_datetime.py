from sqlalchemy.types import DateTime as SA_DateTime
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class DateTime(Declarations.Column):
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
