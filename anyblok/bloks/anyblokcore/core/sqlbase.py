from AnyBlok import target_registry, Core


class SqlBaseException(Exception):
    """ Simple Exception for sql base """


@target_registry(Core)
class SqlBase:

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
    def inserts(cls, *args):
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
