from sqlalchemy.schema import (  # noqa F401
    ForeignKeyConstraint as SQLAForeignKeyConstraint,
    UniqueConstraint as SQLAUniqueConstraint,
    PrimaryKeyConstraint as SQLAPrimaryKeyConstraint,
    CheckConstraint,
    Index as SQLAIndex,
)


def convert_hybrid_property_to_column(hp):
    if isinstance(hp, str):
        return hp

    if hasattr(hp, 'descriptor'):
        if hasattr(hp.descriptor, 'sqla_column'):
            col = hp.descriptor.sqla_column
            if hasattr(col, 'anyblok_field'):
                return hp.key

            return col

    return hp


class ForeignKeyConstraint(SQLAForeignKeyConstraint):

    def __init__(self, columns, refcolumns, *args, **kwargs):
        super().__init__(
            [convert_hybrid_property_to_column(col) for col in columns],
            [convert_hybrid_property_to_column(col) for col in refcolumns],
            *args, **kwargs)


class UniqueConstraint(SQLAUniqueConstraint):

    def __init__(self, *columns, **kwargs):
        super().__init__(
            [convert_hybrid_property_to_column(col) for col in columns],
            **kwargs)


class PrimaryKeyConstraint(SQLAPrimaryKeyConstraint):

    def __init__(self, *columns, **kwargs):
        super().__init__(
            [convert_hybrid_property_to_column(col) for col in columns],
            **kwargs)


class Index(SQLAIndex):

    def __init__(self, *columns, **kwargs):
        super().__init__(
            [convert_hybrid_property_to_column(col) for col in columns],
            **kwargs)
