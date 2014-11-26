from anyblok import Declarations
from sqlalchemy.orm import aliased


@Declarations.target_registry(Declarations.Exception)
class SqlBaseException(Exception):
    """ Simple Exception for sql base """


def query_method(name):

    def wrapper(cls, query, *args, **kwargs):
        return query.sqlalchemy_query_method(name, *args, **kwargs)

    return classmethod(wrapper)


class SqlMixin:
    @classmethod
    def query(cls, *fields):
        res = []
        for f in fields:
            if isinstance(f, str):
                res.append(getattr(cls, f))
            else:
                res.append(f)

        if res:
            return cls.registry.query(*res)

        return cls.registry.query(cls)

    is_sql = True

    @classmethod
    def get_on_model_methods(cls):
        return ['update', 'delete']

    @classmethod
    def aliased(cls, *args, **kwargs):
        return aliased(cls, *args, **kwargs)


@Declarations.target_registry(Declarations.Core)
class SqlBase(SqlMixin):

    sqlalchemy_query_delete = query_method('delete')
    sqlalchemy_query_update = query_method('update')

    def update(self, *args, **kwargs):
        pks = [c.name for c in self.__table__.primary_key.columns.values()]
        where_clause = [getattr(self.__class__, pk) == getattr(self, pk)
                        for pk in pks]
        self.__class__.query().filter(*where_clause).update(*args, **kwargs)

    @classmethod
    def insert(cls, **kwargs):
        instance = cls(**kwargs)
        cls.registry.add(instance)
        cls.registry.flush()
        return instance

    @classmethod
    def multi_insert(cls, *args):
        instances = []
        for kwargs in args:
            if not isinstance(kwargs, dict):
                raise SqlBaseException("inserts method wait list of dict")

            instance = cls(**kwargs)
            cls.registry.add(instance)
            instances.append(instance)

        if instances:
            cls.registry.flush()

        return instances

    @classmethod
    def precommit_hook(cls, method, put_at_the_end_if_exist=False):
        cls.registry.precommit_hook(cls.__registry_name__, method,
                                    put_at_the_end_if_exist)
