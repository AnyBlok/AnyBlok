from anyblok import Declarations
target_registry = Declarations.target_registry
System = Declarations.Model.System
Mixin = Declarations.Mixin
String = Declarations.Column.String
Boolean = Declarations.Column.Boolean


@target_registry(Mixin)
class Field:

    name = String(primary_key=True)
    code = String()
    model = String(primary_key=True)
    label = String()

    @classmethod
    def get_cname(self, field, cname):
        return cname

    @classmethod
    def add_field(cls, name, field, model, table):
        pass

    @classmethod
    def alter_field(cls, field, meta_field):
        pass


@target_registry(System)  # noqa
class Field(Mixin.Field):

    @classmethod
    def add_field(cls, rname, label, model, table):
        vals = dict(code=table + '.' + rname, model=model, name=rname,
                    label=label)
        cls.insert(**vals)

    @classmethod
    def alter_field(cls, field, label):
        field.update({cls.label: label})
