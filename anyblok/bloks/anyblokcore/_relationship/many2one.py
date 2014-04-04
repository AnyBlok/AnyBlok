from anyblok.field import FieldException
from AnyBlok import target_registry, RelationShip
from sqlalchemy.schema import Column as SA_Column
from sqlalchemy.schema import ForeignKey


@target_registry(RelationShip)
class Many2One(RelationShip):

    def __init__(self, **kwargs):
        super(Many2One, self).__init__(**kwargs)
        if kwargs.get('remote_column', None) is None:
            raise FieldException("remote_column is a required argument")

        self.remote_column = self.kwargs.pop('remote_column')

        self.nullable = True
        if 'nullable' in kwargs:
            self.nullable = self.kwargs.pop('nullable')

        if 'one2many' in kwargs:
            self.kwargs['backref'] = self.kwargs.pop('one2many')

        if 'column_name' in kwargs:
            self.column_name = self.kwargs.pop('column_name')
        else:
            self.column_name = "%s_%s" % (self.model.__tablename__,
                                          self.remote_column)

    def update_properties(self, registry, namespace, fieldname, properties):

        self_properties = registry.loaded_namespaces_first_step.get(namespace)
        if self.column_name not in self_properties:
            from sqlalchemy.ext.declarative import declared_attr
            remote_properties = registry.loaded_namespaces_first_step.get(
                self.model.__registry_name__)
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

        self.kwargs['foreign_keys'] = "%s.%s" % (properties['__tablename__'],
                                                 self.column_name)

        return super(Many2One, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)
