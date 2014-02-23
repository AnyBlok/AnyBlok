import AnyBlok
from AnyBlok import target_registry, add_Adapter, Field
from AnyBlok.Interface import ICoreInterface
from anyblok.field import FieldException, AField
from sqlalchemy.orm import relationship
from zope.interface import implementer


@implementer(ICoreInterface)
class ARelationShip(AField):

    __interface__ = 'RelationShip'


add_Adapter(ICoreInterface, ARelationShip)


@target_registry(AnyBlok)
class RelationShip(Field):

    def __init__(self, label=None, model=None, **kwargs):
        self.MustNotBeInstanced(RelationShip)
        super(RelationShip, self).__init__(label=label)

        if model is None:
            raise FieldException("model is required attribut")

        self.model = model.__tablename__
        self.kwargs = kwargs

    def format_foreign_key(self, registry, tablename):
        pass

    def get_sqlalchemy_mapping(self, registry, tablename, properties):
        if 'foreign_keys' in self.kwargs:
            self.format_foreign_key(registry, tablename)

        return relationship(self.model, **self.kwargs)
