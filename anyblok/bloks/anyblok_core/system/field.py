from anyblok import Declarations
target_registry = Declarations.target_registry
Mixin = Declarations.Mixin
String = Declarations.Column.String
Boolean = Declarations.Column.Boolean


@target_registry(Mixin)
class Field:

    name = String(label="Name", primary_key=True)
    code = String(label="Code", unique=True)
    model = String(label="Model", primary_key=True)
    autoincrement = Boolean(label="Auto increment")
    foreign_key = String(label="Foreign key")
    label = String(label="Label")
    nullable = Boolean(label="Nullable")
    primary_key = Boolean(label="Primary key")
    ctype = String(label="Type")
    unique = Boolean(label="Unique")

    @classmethod
    def add_field(cls, cname, column, model, table):
        pass

    @classmethod
    def alter_field(cls, column, meta_column):
        pass
