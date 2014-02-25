from sqlalchemy.types import Unicode
from AnyBlok import target_registry, Column


@target_registry(Column)
class uString(Column):

        def __init__(self, *args, **kwargs):
            size = 64
            if 'size' in kwargs:
                size = kwargs.pop('size')

            self.sqlalchemy_type = Unicode(size)

            super(uString, self).__init__(*args, **kwargs)
