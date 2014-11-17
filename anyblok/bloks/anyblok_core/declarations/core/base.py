from anyblok import Declarations


@Declarations.target_registry(Declarations.Core)
class Base:

    is_sql = False

    @classmethod
    def initialize_model(cls):
        pass

    @classmethod
    def fire(cls, event, *args, **kwargs):
        events = cls.registry.events
        if cls.__registry_name__ in events:
            if event in events[cls.__registry_name__]:
                for model, method in events[cls.__registry_name__][event]:
                    m = cls.registry.loaded_namespaces[model]
                    getattr(m, method)(*args, **kwargs)
