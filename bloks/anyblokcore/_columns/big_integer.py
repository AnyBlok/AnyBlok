from sqlalchemy.types import BigInteger as SA_BigInteger
from AnyBlok import target_registry, Column


@target_registry(Column)
class BigInteger(Column):

    sqlalchemy_type = SA_BigInteger
