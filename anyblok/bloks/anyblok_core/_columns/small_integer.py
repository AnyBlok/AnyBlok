from sqlalchemy.types import SmallInteger as SA_SmallInteger
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class SmallInteger(Declarations.Column):
    """ Small integer column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import SmallInteger

        @target_registry(Model)
        class Test:

            x = SmallInteger(label="Small integer", default=1)

    """
    sqlalchemy_type = SA_SmallInteger
