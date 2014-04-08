# -*- coding: utf-8 -*-
from AnyBlok import target_registry
from AnyBlok.Model import System
from AnyBlok.Column import String, Boolean


@target_registry(System)
class Model:

    name = String(label="Name of the model", size=256, primary_key=True)
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

        for model in cls.registry.loaded_namespaces.keys():
            try:
                # TODO need refactor, then try except pass whenever refactor
                # not apply
                m = cls.registry.loaded_namespaces[model]
                table = m.__tablename__
                if cls.query('name').filter(cls.name == model).count():
                    for cname in m.loaded_columns:
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
                               is_sql_model=is_sql_model)
                    for cname in m.loaded_columns:
                        field = getattr(m, cname)
                        Field = get_field_model(field)
                        Field.add_field(cname, field, model, table)
            except:
                pass
