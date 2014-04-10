from sqlalchemy.types import SmallInteger as SA_SmallInteger
from AnyBlok import target_registry, Column


@target_registry(Column)
class SmallInteger(Column):
    """ Small integer column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import SmallInteger

        @target_registry(Model)
        class Test:

            x = SmallInteger(label="Small integer", default=1)

    """
    sqlalchemy_type = SA_SmallInteger
