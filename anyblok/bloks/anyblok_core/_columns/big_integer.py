from sqlalchemy.types import BigInteger as SA_BigInteger
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class BigInteger(Declarations.Column):
    """ Big integer column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import BigInteger

        @target_registry(Model)
        class Test:

            x = BigInteger(label="Big integer", default=1)

    """
    sqlalchemy_type = SA_BigInteger
