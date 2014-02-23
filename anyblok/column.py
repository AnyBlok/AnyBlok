import AnyBlok
from AnyBlok.Interface import ICoreInterface
from AnyBlok import target_registry, add_Adapter, Field
from anyblok.field import AField
from sqlalchemy.schema import Column as SA_Column
from sqlalchemy.schema import ForeignKey
from zope.interface import implementer


@implementer(ICoreInterface)
class AColumn(AField):

    __interface__ = 'Column'


add_Adapter(ICoreInterface, AColumn)


@target_registry(AnyBlok)
class Column(Field):

    foreign_key = None
    foreign_key_code = None
    sqlalchemy_type = None

    def __init__(self, label=None, *args, **kwargs):
        self.MustNotBeInstanced(Column)
        assert self.sqlalchemy_type

        if 'type_' in kwargs:
            del kwargs['type_']
        if 'foreign_key' in kwargs:
            model, col = kwargs.pop('foreign_key')
            self.foreign_key = model.__tablename__ + '.' + col
            self.foreign_key_code = model.__namespace__ + ' - ' + col

        self.args = args
        self.kwargs = kwargs
        super(Column, self).__init__(label=label)

    def get_sqlalchemy_mapping(self, registry, tablename, properties):
        args = self.args
        if self.foreign_key:
            args = args + (ForeignKey(self.foreign_key),)

        return SA_Column(self.sqlalchemy_type, *args, **self.kwargs)
