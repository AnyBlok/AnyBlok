from sqlalchemy.schema import Column as SA_Column
from sqlalchemy.schema import ForeignKey
from anyblok import Declarations


@Declarations.target_registry(Declarations.RelationShip)
class Many2One(Declarations.RelationShip):
    """ Define a relation ship attribute on the model

    ::

        @target_registry(Model)
        class TheModel:

            relationship = Many2One(label="The relation ship",
                                    model=Model.RemoteModel,
                                    remote_column="The remote column",
                                    column_name="The column which have the "
                                                "foreigh key",
                                    nullable=False,
                                    one2many="themodels")

    If the remote_column are not define then, the system take the primary key
    of the remote model

    If the column doesn't exist, then the column will be create. Use the
    nullable option.
    If the name has not filled then the name is "'remote table'_'remote colum'"

    :param model: the remote model
    :param remote_column: the column name on the remote model
    :param column_name: the column on the model which have the foreign key
    :param nullable: If the column_name is nullable
    :param one2many: create the one2many link with this many2one
    """

    def __init__(self, **kwargs):
        super(Many2One, self).__init__(**kwargs)

        self.remote_column = None
        if 'remote_column' in kwargs:
            self.remote_column = self.kwargs.pop('remote_column')

        self.nullable = True
        if 'nullable' in kwargs:
            self.nullable = self.kwargs.pop('nullable')
            self.kwargs['info']['nullable'] = self.nullable

        if 'one2many' in kwargs:
            self.kwargs['backref'] = self.kwargs.pop('one2many')
            self.kwargs['info']['remote_name'] = self.kwargs['backref']

        self.column_name = None
        if 'column_name' in kwargs:
            self.column_name = self.kwargs.pop('column_name')

    def update_properties(self, registry, namespace, fieldname, properties):
        """ Create the column which have the foreign key if the column doesn't
        exist

        :param registry: the registry which load the relation ship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relation ship
        :param propertie: the properties known
        """
        remote_properties = registry.loaded_namespaces_first_step.get(
            self.model.__registry_name__)

        if self.remote_column is None:
            self.remote_column = self.find_primary_key(remote_properties)

        self.kwargs['info']['remote_column'] = self.remote_column

        if self.column_name is None:
            self.column_name = "%s_%s" % (self.model.__tablename__,
                                          self.remote_column)

        self.kwargs['info']['local_column'] = self.column_name

        self_properties = registry.loaded_namespaces_first_step.get(namespace)
        if self.column_name not in self_properties:
            from sqlalchemy.ext.declarative import declared_attr
            remote_type = remote_properties[self.remote_column].native_type()
            foreign_key = '%s.%s' % (self.model.__tablename__,
                                     self.remote_column)

            def wraper(cls):
                return SA_Column(
                    remote_type, ForeignKey(foreign_key),
                    nullable=self.nullable,
                    info=dict(label=self.label, foreign_key=foreign_key))

            properties[self.column_name] = declared_attr(wraper)

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Create the relation ship

        :param registry: the registry which load the relation ship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relation ship
        :param propertie: the properties known
        :rtype: Many2One relation ship
        """
        self.kwargs['foreign_keys'] = "%s.%s" % (properties['__tablename__'],
                                                 self.column_name)

        return super(Many2One, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)
