print("plop")
from anyblok import AnyBlok


@AnyBlok.target_registry(AnyBlok.Core)
class Base:

    @classmethod
    def is_sql_model(self):
        return False
