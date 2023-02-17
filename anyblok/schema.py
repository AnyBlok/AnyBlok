from sqlalchemy.schema import (  # noqa F401
    ForeignKeyConstraint as SQLAForeignKeyConstraint,
    UniqueConstraint as SQLAUniqueConstraint,
    PrimaryKeyConstraint as SQLAPrimaryKeyConstraint,
    Index as SQLAIndex,
)


class ForeignKeyConstraint(SQLAForeignKeyConstraint):

    def __init__(self, columns, refcolumns, *args, **kwargs):
        super().__init__(
            [
                (
                    col.descriptor.sqla_column
                    if hasattr(col.descriptor, 'sqla_column')
                    else col
                )
                for col in columns
            ],
            [
                (
                    col.descriptor.sqla_column
                    if hasattr(col.descriptor, 'sqla_column')
                    else col
                )
                for col in refcolumns
            ],
            *args, **kwargs)


class UniqueConstraint(SQLAUniqueConstraint):

    def __init__(self, *columns, **kwargs):
        super().__init__(
            [
                (
                    col.descriptor.sqla_column
                    if hasattr(col.descriptor, 'sqla_column')
                    else col
                )
                for col in columns
            ],
            **kwargs)


class PrimaryKeyConstraint(SQLAPrimaryKeyConstraint):

    def __init__(self, *columns, **kwargs):
        super().__init__(
            [
                (
                    col.descriptor.sqla_column
                    if hasattr(col.descriptor, 'sqla_column')
                    else col
                )
                for col in columns
            ],
            **kwargs)


class Index(SQLAIndex):

    def __init__(self, *columns, **kwargs):
        super().__init__(
            [
                (
                    col.descriptor.sqla_column
                    if hasattr(col.descriptor, 'sqla_column')
                    else col
                )
                for col in columns
            ],
            **kwargs)
