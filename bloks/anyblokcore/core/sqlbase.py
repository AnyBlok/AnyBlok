from AnyBlok import target_registry, Core


@target_registry(Core)
class SqlBase(object):

    @classmethod
    def is_sql_model(self):
        return True
