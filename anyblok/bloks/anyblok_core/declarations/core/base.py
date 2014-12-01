from anyblok import Declarations


@Declarations.target_registry(Declarations.Core)
class Base:
    """ this class is inherited by all the model
    """

    is_sql = False

    @classmethod
    def initialize_model(cls):
        """ This method is called to initialize a model at the creation of the
        registry
        """
        pass

    @classmethod
    def fire(cls, event, *args, **kwargs):
        """ Call a specific event  on the model

        :param event: Name of the event
        """
        events = cls.registry.events
        if cls.__registry_name__ in events:
            if event in events[cls.__registry_name__]:
                for model, method in events[cls.__registry_name__][event]:
                    m = cls.registry.loaded_namespaces[model]
                    getattr(m, method)(*args, **kwargs)
