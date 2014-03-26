from AnyBlok import target_registry, Core  # , Model
from sqlalchemy.orm import Session as SA_Session
# from sqlalchemy.orm import query


@target_registry(Core)
class Session(SA_Session):

    def __init__(self, *args, **kwargs):
        # kwargs['query_cls'] = self.registry.Query
        super(Session, self).__init__(*args, **kwargs)
