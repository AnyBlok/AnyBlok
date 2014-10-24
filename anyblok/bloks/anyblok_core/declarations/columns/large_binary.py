from sqlalchemy.types import LargeBinary as SA_LargeBinary
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class LargeBinary(Declarations.Column):
    """ Large binary column

    ::

        from os import urandom
        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        LargeBinary = Declarations.Column.LargeBinary

        blob = urandom(100000)

        @target_registry(Model)
        class Test:

            x = LargeBinary(default=blob)

    """
    sqlalchemy_type = SA_LargeBinary
