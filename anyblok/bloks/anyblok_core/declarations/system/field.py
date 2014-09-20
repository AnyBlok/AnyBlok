from anyblok import Declarations
target_registry = Declarations.target_registry
Mixin = Declarations.Mixin
String = Declarations.Column.String
Boolean = Declarations.Column.Boolean


@target_registry(Mixin)
class Field:

    name = String(primary_key=True)
    code = String()
    model = String(primary_key=True)
    label = String()
    nullable = Boolean()

    @classmethod
    def add_field(cls, name, field, model, table):
        pass

    @classmethod
    def alter_field(cls, field, meta_field):
        pass
