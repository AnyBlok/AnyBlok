from anyblok import Declarations
target_registry = Declarations.target_registry
System = Declarations.Model.System
Mixin = Declarations.Mixin
String = Declarations.Column.String
Boolean = Declarations.Column.Boolean


@target_registry(System)
class Column(Mixin.Field):

    autoincrement = Boolean(label="Auto increment")
    foreign_key = String()
    primary_key = Boolean()
    ctype = String(label="Type")
    unique = Boolean()

    @classmethod
    def get_cname(self, field, cname):
        return field.property.columns[0].name

    @classmethod
    def add_field(cls, cname, column, model, table):
        c = column.property.columns[0]
        vals = dict(autoincrement=c.autoincrement,
                    code=table + '.' + cname,
                    model=model, name=cname,
                    foreign_key=c.info.get('foreign_key'),
                    label=c.info['label'],
                    nullable=c.nullable,
                    primary_key=c.primary_key,
                    ctype=str(c.type),
                    unique=c.unique)
        cls.insert(**vals)

    @classmethod
    def alter_field(cls, column, meta_column):
        c = meta_column.property.columns[0]
        for col in ('autoincrement', 'nullable', 'primary_key', 'unique'):
            if getattr(column, col) != getattr(c, col):
                setattr(column, col, getattr(c, col))

        for col in ('foreign_key', 'label'):
            if getattr(column, col) != c.info.get(col):
                setattr(column, col, c.info.get(col))

        ctype = str(c.type)
        if column.ctype != ctype:
            column.ctype = ctype
