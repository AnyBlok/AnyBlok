# -*- coding: utf-8 -*-
from AnyBlok import target_registry
from AnyBlok.Model import System
from AnyBlok.Column import String, Boolean


@target_registry(System)
class Column:

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
    def add_column(cls, cname, column, model, table):
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
    def alter_column(cls, column, meta_column):
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
