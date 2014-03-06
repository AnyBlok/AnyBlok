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
        Column = cls.registry.System.Column
        for model in cls.registry.loaded_namespaces.keys():
            m = cls.registry.loaded_namespaces[model]
            table = m.__tablename__
            if cls.query('name').filter(cls.name == model).count():
                for cname in m.loaded_columns:
                    column = getattr(m, cname)
                    query = Column.query()
                    query = query.filter(Column.model == model)
                    query = query.filter(Column.name == cname)
                    if query.count():
                        Column.alter_column(query.first(), column)
                    else:
                        Column.add_column(cname, column, model, table)
            else:
                is_sql_model = len(m.loaded_columns) > 0
                cls.insert(name=model, table=table, is_sql_model=is_sql_model)
                for cname in m.loaded_columns:
                    column = getattr(m, cname)
                    Column.add_column(cname, column, model, table)
