from sqlalchemy import types, util, sql
from sqlalchemy.sql.operators import custom_op
import json
from anyblok import Declarations


json_null = object()


class JsonElement(sql.elements.BinaryExpression):
    """Represents accessing an element of a :class:`.JSON` value.

    The :class:`.JSONElement` is produced whenever using the Python index
    operator on an expression that has the type :class:`.JSON`::

        expr = mytable.c.json_data['some_key']

    The expression typically compiles to a JSON access such as ``col -> key``.
    Modifiers are then available for typing behavior, including
    :meth:`.JSONElement.cast` and :attr:`.JSONElement.astext`.

    """

    def __init__(self, left, right, astext=False,
                 opstring=None, result_type=None):
        self._astext = astext
        if opstring is None:
            if hasattr(right, '__iter__') and \
                    not isinstance(right, util.string_types):
                opstring = "#>"
                right = "{%s}" % (
                    ", ".join(util.text_type(elem) for elem in right))
            else:
                opstring = "->"

        self._json_opstring = opstring
        operator = custom_op(opstring, precedence=5)
        right = left._check_literal(left, operator, right)
        super(JsonElement, self).__init__(
            left, right, operator, type_=result_type)

    @property
    def astext(self):
        """Convert this :class:`.JSONElement` to use the 'astext' operator
        when evaluated.

        E.g.::

            select([data_table.c.data['some key'].astext])

        .. seealso::

            :meth:`.JSONElement.cast`

        """
        if self._astext:
            return self
        else:
            return JsonElement(
                self.left,
                self.right,
                astext=True,
                opstring=self._json_opstring + ">",
                result_type=sql.sqltypes.String(convert_unicode=True)
            )

    def cast(self, type_):
        """Convert this :class:`.JSONElement` to apply both the 'astext' operator
        as well as an explicit type cast when evaulated.

        E.g.::

            select([data_table.c.data['some key'].cast(Integer)])

        .. seealso::

            :attr:`.JSONElement.astext`

        """
        if not self._astext:
            return self.astext.cast(type_)
        else:
            return sql.cast(self, type_)


class JsonType(types.TypeDecorator):
    impl = types.Unicode

    class comparator_factory(sql.sqltypes.Concatenable.Comparator):
        """Define comparison operations for :class:`.JSON`."""

        def __getitem__(self, other):
            """Get the value at a given key."""

            return JsonElement(self.expr, other)

        def _adapt_expression(self, op, other_comparator):
            if isinstance(op, custom_op):
                if op.opstring == '->':
                    return op, sql.sqltypes.Text
            return sql.sqltypes.Concatenable.Comparator._adapt_expression(
                self, op, other_comparator)

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
