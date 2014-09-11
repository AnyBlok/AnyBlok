from anyblok import Declarations
from sqlalchemy.orm import query
from inspect import ismethod


@Declarations.target_registry(Declarations.Exception)
class QueryException(Exception):
    """ Simple Exception for query """


@Declarations.target_registry(Declarations.Core)
class Query(query.Query):

    def all(self):
        return self.registry.InstrumentedList(self)

    def sqlalchemy_query_method(self, method, *args, **kwargs):
        return getattr(query.Query, method)(self, *args, **kwargs)

    @classmethod
    def get_on_model_methods(cls):
        return ['update', 'delete']

    def __getattribute__(self, name):
        validate = False
        if name in Query.get_on_model_methods():
            try:
                entity = self._primary_entity.mapper.entity
            except:
                pass
            else:
                if name in entity.get_on_model_methods():
                    if hasattr(entity, name):
                        validate = True

        if validate:

            def wrapper(*args, **kwargs):
                if ismethod(getattr(entity, name)):
                    return getattr(entity, name)(self, *args, **kwargs)
                else:
                    raise QueryException("%s.%s must be a classmethod" % (
                        entity, name))

            return wrapper
        else:
            return super(Query, self).__getattribute__(name)
