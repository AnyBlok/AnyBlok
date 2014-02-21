from anyblok import AnyBlok


@AnyBlok.target_registry(AnyBlok.Core)
class SqlBase(object):

    @classmethod
    def is_sql_model(self):
        return True
