from AnyBlok import target_registry, Core


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
