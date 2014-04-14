from sqlalchemy.types import Text as SA_Text
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Text(Declarations.Column):
    """ Text column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Text

        @target_registry(Model)
        class Test:

            x = Text(label="Text", default='test')

    """
    sqlalchemy_type = SA_Text
