from sqlalchemy.types import Boolean as SA_Boolean
from AnyBlok import target_registry, Column


@target_registry(Column)
class Boolean(Column):
    """ Boolean column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Boolean

        @target_registry(Model)
        class Test:

            x = Boolean(label="Boolean", default=True)

    """
    sqlalchemy_type = SA_Boolean
