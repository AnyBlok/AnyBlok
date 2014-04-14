from sqlalchemy.types import Integer as SA_Integer
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Integer(Declarations.Column):
    """ Integer column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Integer

        @target_registry(Model)
        class Test:

            x = Integer(label="Integer", default=1)

    """
    sqlalchemy_type = SA_Integer
