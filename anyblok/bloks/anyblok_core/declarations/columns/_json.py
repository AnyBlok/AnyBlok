from sqlalchemy import types
import json
from anyblok import Declarations


json_null = object()


class JsonType(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        if value is json_null:
            value = None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


@Declarations.target_registry(Declarations.Column)
class Json(Declarations.Column):
    """ String column

    ::

        from AnyBlok import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        String = Declarations.Column.String

        @target_registry(Model)
        class Test:

            x = String(default='test')

    """
    sqlalchemy_type = JsonType
    Null = json_null
