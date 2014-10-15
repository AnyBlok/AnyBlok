from sqlalchemy.types import Unicode
from anyblok import Declarations


@Declarations.target_registry(Declarations.Column)
class uString(Declarations.Column):
    """ Unicode column

    ::

        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        uString = Declarations.uString

        @target_registry(Model)
        class Test:

            x = uString(de", default=u'test')

    """
    def __init__(self, *args, **kwargs):
        size = 64
        if 'size' in kwargs:
            size = kwargs.pop('size')

        self.sqlalchemy_type = Unicode(size)

        super(uString, self).__init__(*args, **kwargs)
