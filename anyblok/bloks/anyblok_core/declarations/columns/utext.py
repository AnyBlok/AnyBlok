from sqlalchemy.types import UnicodeText
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class uText(Declarations.Column):
    """ Unicode text column

    ::

        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        uText = Declarations.Column.uText

        @target_registry(Model)
        class Test:

            x = uText(default=u'test')

    """
    sqlalchemy_type = UnicodeText
