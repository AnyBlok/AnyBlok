from anyblok import Declarations


@Declarations.target_registry(Declarations.Core)
class InstrumentedList:
    """ class of the return of the query.all() or the relationship list
    """

    def __getattr__(self, name):

        def wrapper(*args, **kwargs):
            return [getattr(x, name)(*args, **kwargs) for x in self]

        if not self:
            return []
        elif hasattr(getattr(self[0], name), '__call__'):
            return wrapper
        else:
            return [getattr(x, name) for x in self]
