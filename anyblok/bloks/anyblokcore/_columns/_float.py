from sqlalchemy.types import Float as SA_Float
from AnyBlok import target_registry, Column


@target_registry(Column)
class Float(Column):
    """ Float column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Float

        @target_registry(Model)
        class Test:

            x = Float(label="Float", default=1.0)

    """
    sqlalchemy_type = SA_Float
