from anyblok.field import FieldException
from AnyBlok import target_registry, RelationShip


@target_registry(RelationShip)
class Many2One(RelationShip):

    def format_foreign_key(self, registry, tablename):
        fk = self.kwargs['foreign_keys']
        if not isinstance(fk, str):
            raise FieldException("For many2one foreign_keys must br a str")

        if len(fk.split('.')) == 2:
            return

        self.kwargs['foreign_keys'] = tablename + '.' + fk
