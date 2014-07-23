from anyblok import Declarations
from logging import getLogger
from sqlalchemy.orm.attributes import InstrumentedAttribute
from inspect import getmembers

logger = getLogger(__name__)

target_registry = Declarations.target_registry
System = Declarations.Model.System
String = Declarations.Column.String
Text = Declarations.Column.Text
Boolean = Declarations.Column.Boolean


@target_registry(System)
class Model:
    """Models assembled"""

    def __str__(self):
        if self.description:
            return self.description

        return self.name

    name = String(label="Name of the model", size=256, primary_key=True)
    description = Text(label="Description")
    table = String(label="Name of the table", size=256)
    is_sql_model = Boolean(label="Is a SQL model")

    @classmethod
    def update_list(cls):

        def get_field_model(field):
            ftype = field.property.__class__.__name__
            if ftype == 'ColumnProperty':
                return cls.registry.System.Column
            elif ftype == 'RelationshipProperty':
                return cls.registry.System.RelationShip
            else:
                raise Exception('Not implemented yet')

        def get_fields(model):
            m = getmembers(model)
            res = [x for x, y in m if type(y) is InstrumentedAttribute]
            return res

        for model in cls.registry.loaded_namespaces.keys():
            try:
                # TODO need refactor, then try except pass whenever refactor
                # not apply
                m = cls.registry.loaded_namespaces[model]
                table = m.__tablename__
                _m = cls.query('name').filter(cls.name == model)
                if _m.count():
                    _m.update({'description': m.__doc__})
                    for cname in get_fields(m):
                        field = getattr(m, cname)
                        Field = get_field_model(field)
                        query = Field.query()
                        query = query.filter(Field.model == model)
                        query = query.filter(Field.name == cname)
                        if query.count():
                            Field.alter_field(query.first(), field)
                        else:
                            Field.add_field(cname, field, model, table)
                else:
                    is_sql_model = len(m.loaded_columns) > 0
                    cls.insert(name=model, table=table,
                               is_sql_model=is_sql_model,
                               description=m.__doc__)
                    for cname in get_fields(m):
                        field = getattr(m, cname)
                        Field = get_field_model(field)
                        Field.add_field(cname, field, model, table)
            except Exception as e:
                logger.error(str(e))
