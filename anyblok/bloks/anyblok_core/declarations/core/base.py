from anyblok import Declarations


@Declarations.target_registry(Declarations.Core)
class Base:

    is_sql = False

    @classmethod
    def initialize_model(cls):
        pass
