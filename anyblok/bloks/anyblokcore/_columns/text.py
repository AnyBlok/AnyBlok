from sqlalchemy.types import Text as SA_Text
from AnyBlok import target_registry, Column


@target_registry(Column)
class Text(Column):
    """ Text column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Text

        @target_registry(Model)
        class Test:

            x = Text(label="Text", default='test')

    """
    sqlalchemy_type = SA_Text
