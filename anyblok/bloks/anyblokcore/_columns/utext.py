from sqlalchemy.types import UnicodeText
from AnyBlok import target_registry, Column


@target_registry(Column)
class uText(Column):
    """ Unicode text column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import uText

        @target_registry(Model)
        class Test:

            x = uText(label="Unicode text", default=u'test')

    """
    sqlalchemy_type = UnicodeText
