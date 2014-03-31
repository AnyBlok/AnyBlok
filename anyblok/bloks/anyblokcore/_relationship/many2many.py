from AnyBlok import RelationShip, target_registry
from sqlalchemy import Table, Column, ForeignKey


@target_registry(RelationShip)
class Many2Many(RelationShip):

    def get_sqlalchemy_mapping(self, registry, tablename, fieldname,
                               properties):
        if 'columnjoined' in self.kwargs:
            jointablename, fromcolumn, tocolumn = self.kwargs.pop(
                'columnjoined')
            if not hasattr(registry, 'many2many_tables'):
                setattr(registry, 'many2many_tables', {})

            if jointablename in registry.many2many_tables:
                self.kwargs['secondary'] = registry.many2many_tables[
                    jointablename]
            else:
                t = Table(jointablename, registry.declarativebase.metadata,
                          Column(
                              fromcolumn[2],
                              fromcolumn[0].sqlalchemy_type,
                              ForeignKey(tablename + '.' + fromcolumn[1])),
                          Column(
                              tocolumn[2],
                              tocolumn[0].sqlalchemy_type,
                              ForeignKey(self.model + '.' + tocolumn[1])))
                self.kwargs['secondary'] = t
                registry.many2many_tables[jointablename] = t
                self.kwargs['foreign_keys'] = jointablename + '.'
                self.kwargs['foreign_keys'] += fromcolumn[2]

        return super(Many2Many, self).get_sqlalchemy_mapping(
            registry, tablename, fieldname, properties)
