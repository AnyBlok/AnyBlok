from AnyBlok import target_registry
from AnyBlok import Mixin
from AnyBlok.Column import String, Boolean


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
