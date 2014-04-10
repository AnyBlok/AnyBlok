from sqlalchemy.types import Integer as SA_Integer
from AnyBlok import target_registry, Column


@target_registry(Column)
class Integer(Column):
    """ Integer column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Integer

        @target_registry(Model)
        class Test:

            x = Integer(label="Integer", default=1)

    """
    sqlalchemy_type = SA_Integer
