from anyblok.field import FieldException
from AnyBlok import RelationShip, target_registry
from sqlalchemy.orm import backref

# FIXME cause of refactore relation ship api


@target_registry(RelationShip)
class One2One(RelationShip.Many2One):

    def __init__(self, **kwargs):
        super(One2One, self).__init__(**kwargs)

        if 'backref' not in kwargs:
            raise FieldException("backref is a required argument")

        if 'one2many' in kwargs:
            raise FieldException("Unknow argmument 'one2many'")

        self.kwargs['backref'] = backref(
            self.kwargs['backref'], uselist=False)
