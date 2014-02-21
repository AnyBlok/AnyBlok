from AnyBlok import target_registry, Core


@target_registry(Core)
class Base:

    @classmethod
    def is_sql_model(self):
        return False
