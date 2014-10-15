from sqlalchemy.types import Text as SA_Text
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class Text(Declarations.Column):
    """ Text column

    ::

        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Text = Declarations.Text

        @target_registry(Model)
        class Test:

            x = Text(default='test')

    """
    sqlalchemy_type = SA_Text
