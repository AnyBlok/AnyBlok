import AnyBlok
from AnyBlok import target_registry, add_Adapter, Field
from AnyBlok.Interface import ICoreInterface
from anyblok.field import FieldException, AField
from sqlalchemy.orm import relationship
from zope.interface import implementer


@implementer(ICoreInterface)
class ARelationShip(AField):
    """ Adapter to Field Class

    The RelationShip class are used to define type of AnyBlok SQL field

    Add new relation ship type::

        @target_registry(RelationShip)
        class Many2one:
            pass

    the relation ship column are forbidden because the model can be used on
    the model
    """

    __interface__ = 'RelationShip'


add_Adapter(ICoreInterface, ARelationShip)


@target_registry(AnyBlok)
class RelationShip(Field):
    """ Relation Ship class

    This class can't be instancied
    """

    def __init__(self, label=None, model=None, **kwargs):
        self.MustNotBeInstanced(RelationShip)
        super(RelationShip, self).__init__(label=label)

        if model is None:
            raise FieldException("model is required attribut")

        self.model = model.__tablename__
        self.kwargs = kwargs

    def format_foreign_key(self, registry, tablename):
        """ Format the foreign key

        :param registry: current registry
        :param tablename: table name of the model
        """
        pass

    def get_sqlalchemy_mapping(self, registry, tablename, fieldname,
                               properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param tablename: table name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        """
        if 'foreign_keys' in self.kwargs:
            self.format_foreign_key(registry, tablename)

        return relationship(self.model, **self.kwargs)
