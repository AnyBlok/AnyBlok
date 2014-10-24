from sqlalchemy.types import DateTime as SA_DateTime
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class DateTime(Declarations.Column):
    """ DateTime column

    ::

        from datetime import datetime
        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        DateTime = Declarations.Column.DateTime

        @target_registry(Model)
        class Test:

            x = DateTime(default=datetime.now())

    """
    sqlalchemy_type = SA_DateTime
