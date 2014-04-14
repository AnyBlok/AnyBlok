from anyblok import Declarations
target_registry = Declarations.target_registry
System = Declarations.Model.System
Mixin = Declarations.Mixin


@target_registry(System)
class RelationShip(Mixin.Field):
    pass
    # TODO
