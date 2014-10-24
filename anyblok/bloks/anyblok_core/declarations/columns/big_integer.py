from sqlalchemy.types import BigInteger as SA_BigInteger
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class BigInteger(Declarations.Column):
    """ Big integer column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        BigInteger = Declarations.Column.BigInteger

        @target_registry(Model)
        class Test:

            x = BigInteger(default=1)

    """
    sqlalchemy_type = SA_BigInteger
