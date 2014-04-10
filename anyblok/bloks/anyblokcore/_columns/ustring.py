from sqlalchemy.types import Unicode
from AnyBlok import target_registry, Column


@target_registry(Column)
class uString(Column):
    """ Unicode column

    ::

        from AnyBlok import target_registry, Model
        from AnyBlok.Column import uString

        @target_registry(Model)
        class Test:

            x = uString(label="Unicode", default=u'test')

    """
    def __init__(self, *args, **kwargs):
        size = 64
        if 'size' in kwargs:
            size = kwargs.pop('size')

        self.sqlalchemy_type = Unicode(size)

        super(uString, self).__init__(*args, **kwargs)
