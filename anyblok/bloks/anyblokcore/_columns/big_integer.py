from sqlalchemy.types import BigInteger as SA_BigInteger
from AnyBlok import target_registry, Column


@target_registry(Column)
class BigInteger(Column):
    """ Big integer column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import BigInteger

        @target_registry(Model)
        class Test:

            x = BigInteger(label="Big integer", default=1)

    """
    sqlalchemy_type = SA_BigInteger
