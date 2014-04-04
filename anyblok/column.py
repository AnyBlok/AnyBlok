import AnyBlok
from AnyBlok.Interface import ICoreInterface
from AnyBlok import target_registry, add_Adapter, Field
from anyblok.field import AField
from sqlalchemy.schema import Column as SA_Column
from sqlalchemy.schema import ForeignKey
from zope.interface import implementer


@implementer(ICoreInterface)
class AColumn(AField):
    """ Adapter to Field Class

    The Column class are used to define type of AnyBlok SQL field

    Add new column type::

        @target_registry(Column)
        class Integer:

            sqlalchemy_type = sqlalchemy.Integer

    the remove column are forbidden because the model can be used on the model
    """

    __interface__ = 'Column'


add_Adapter(ICoreInterface, AColumn)


@target_registry(AnyBlok)
class Column(Field):
    """ Column class

    This class can't be instancied
    """

    foreign_key = None
    sqlalchemy_type = None

    def __init__(self, *args, **kwargs):
        """ Initialise the column

        :param label: label of this field
        :type label: str
        """
        self.MustNotBeInstanced(Column)
        assert self.sqlalchemy_type

        label = None

        if 'label' in kwargs:
            label = kwargs.pop('label')

        if 'type_' in kwargs:
            del kwargs['type_']

        if 'foreign_key' in kwargs:
            model, col = kwargs.pop('foreign_key')
            self.foreign_key = model.__tablename__ + '.' + col

        self.args = args
        self.kwargs = kwargs
        super(Column, self).__init__(label=label)

    def native_type(cls):
        """ Return the native SqlAlchemy type """
        return cls.sqlalchemy_type

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties, forceaddname=False):
        """ Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        :param forceaddname: boolean if True the name of the field will be put
            on the declaration of the column
        :rtype: sqlalchemy column instance
        """
        args = self.args

        kwargs = self.kwargs.copy()
        if 'info' not in kwargs:
            kwargs['info'] = {}

        kwargs['info']['label'] = self.label

        if self.foreign_key:
            args = args + (ForeignKey(self.foreign_key),)
            kwargs['info']['foreign_key'] = self.foreign_key

        if forceaddname:
            return SA_Column(fieldname, self.sqlalchemy_type, *args, **kwargs)

        return SA_Column(self.sqlalchemy_type, *args, **kwargs)
