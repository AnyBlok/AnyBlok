from anyblok import Declarations
from .sqlbase import SqlMixin


@Declarations.target_registry(Declarations.Exception)
class ViewException(Exception):
    """ Simple Exception for sql view base """


def query_method(name):

    def wrapper(cls, query, *args, **kwargs):
        raise ViewException("%r.%r method are not availlable on view model" % (
            cls, name))

    return classmethod(wrapper)


@Declarations.target_registry(Declarations.Core)
class SqlViewBase(SqlMixin):

    sqlalchemy_query_delete = query_method('delete')
    sqlalchemy_query_update = query_method('update')
