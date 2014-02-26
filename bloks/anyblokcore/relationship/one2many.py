from AnyBlok import target_registry, RelationShip


@target_registry(RelationShip)
class One2Many(RelationShip):

    def get_sqlalchemy_mapping(self, registry, tablename):
        if 'columnjoined' in self.kwargs:
            fromcolumn, tocolumn = self.kwargs.pop('columnjoined')
            if 'primaryjoin' not in self.kwargs:
                primaryjoin = tablename + '.' + fromcolumn + " == "
                primaryjoin += self.model + '.' + tocolumn
                self.kwargs['primaryjoin'] = primaryjoin

        return super(One2Many, self).get_sqlalchemy_mapping(registry,
                                                            tablename)
