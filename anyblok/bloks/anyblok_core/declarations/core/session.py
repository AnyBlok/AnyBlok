from sqlalchemy.orm import Session as SA_Session
from anyblok import Declarations


@Declarations.target_registry(Declarations.Core)
class Session(SA_Session):
    """ Overload of the SqlAlchemy session
    """

    def __init__(self, *args, **kwargs):
        kwargs['query_cls'] = self.registry_query
        super(Session, self).__init__(*args, **kwargs)
