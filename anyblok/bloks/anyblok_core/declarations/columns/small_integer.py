from sqlalchemy.types import SmallInteger as SA_SmallInteger
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class SmallInteger(Declarations.Column):
    """ Small integer column

    ::

        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        SmallInteger = Declarations.SmallInteger

        @target_registry(Model)
        class Test:

            x = SmallInteger(default=1)

    """
    sqlalchemy_type = SA_SmallInteger
