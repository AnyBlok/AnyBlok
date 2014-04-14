from sqlalchemy.types import String as SA_String
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class String(Declarations.Column):
    """ String column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import String

        @target_registry(Model)
        class Test:

            x = String(label="String", default='test')

    """
    def __init__(self, *args, **kwargs):
        size = 64
        if 'size' in kwargs:
            size = kwargs.pop('size')

        self.sqlalchemy_type = SA_String(size)

        super(String, self).__init__(*args, **kwargs)
