from anyblok import Declarations


@Declarations.target_registry(Declarations.Exception)
class SqlBaseException(Exception):
    """ Simple Exception for sql base """


def query_method(name):

    def wrapper(cls, query, *args, **kwargs):
        return query.sqlalchemy_query_method(name, *args, **kwargs)

    return classmethod(wrapper)


@Declarations.target_registry(Declarations.Core)
class SqlBase:

    is_sql = True

    @classmethod
    def get_on_model_methods(cls):
        return ['update', 'delete']

    delete = query_method('delete')

    @classmethod
    def update(cls, query, **kwargs):
        return query.sqlalchemy_query_method('update', kwargs)

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
