from anyblok import Declarations


@Declarations.target_registry(Declarations.Exception)
class SqlBaseException(Exception):
    """ Simple Exception for sql base """
