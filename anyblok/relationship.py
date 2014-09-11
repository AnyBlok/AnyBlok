from anyblok import Declarations
from sqlalchemy.orm import relationship


FieldException = Declarations.Exception.FieldException


@Declarations.add_declaration_type()
class RelationShip(Declarations.Field):
    """ Relation Ship class

    The RelationShip class are used to define type of Declarations SQL field

    Add new relation ship type::

        @Declarations.target_registry(Declarations.RelationShip)
        class Many2one:
            pass

    the relation ship column are forbidden because the model can be used on
    the model
    """

    def __init__(self, label=None, model=None, **kwargs):
        self.MustNotBeInstanced(RelationShip)
        super(RelationShip, self).__init__(label=label)

        if model is None:
            raise FieldException("model is required attribut")

        if 'info' not in kwargs:
            kwargs['info'] = {}

        kwargs['info']['label'] = self.label
        kwargs['info']['remote_model'] = model.__registry_name__

        self.model = model
        self.kwargs = kwargs

    def apply_instrumentedlist(self, registry):
        self.kwargs['collection_class'] = registry.InstrumentedList
        backref = self.kwargs.get('backref')
        if not backref:
            return

        if not isinstance(backref, (list, tuple)):
            backref = (backref, {})

        backref[1]['collection_class'] = registry.InstrumentedList
        self.kwargs['backref'] = backref

    def find_primary_key(self, properties):
        """ Return the primary key come from the first step property

        :param properties: first step properties for the model
        :rtype: column name of the primary key
        """
        pks = []
        for f, p in properties.items():
            if 'primary_key' in p.kwargs:
                pks.append(f)

        if len(pks) != 1:
            raise FieldException(
                "We must have one and only one primary key")

        return pks[0]

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        :rtype: sqlalchemy relation ship instance
        """
        self.kwargs['info']['rtype'] = self.__class__.__name__
        self.apply_instrumentedlist(registry)
        return relationship(self.model.__tablename__, **self.kwargs)
