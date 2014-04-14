from sqlalchemy.types import Boolean as SA_Boolean
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Boolean(Declarations.Column):
    """ Boolean column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Boolean

        @target_registry(Model)
        class Test:

            x = Boolean(label="Boolean", default=True)

    """
    sqlalchemy_type = SA_Boolean
