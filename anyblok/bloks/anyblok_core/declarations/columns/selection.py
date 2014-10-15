from anyblok import Declarations
from sqlalchemy import types
from sqlalchemy.ext.hybrid import hybrid_property


FieldException = Declarations.Exception.FieldException


class StrSelection(str):
    selections = {}

    def validate(self):
        a = super(StrSelection, self).__str__()
        return a in self.selections.keys()

    @property
    def label(self):
        a = super(StrSelection, self).__str__()
        return self.selections[a]


class SelectionType(types.UserDefinedType):

    def __init__(self, selections, size):
        super(SelectionType, self).__init__()
        self.size = size
        if isinstance(selections, dict):
            self.selections = selections
        elif isinstance(selections, (list, tuple)):
            self.selections = dict(selections)
        else:
            raise FieldException(
                "selection wainting 'dict', get %r" % type(selections))

        for k in self.selections.keys():
            if len(k) > 64:
                raise Exception(
                    '%r is too long %r, waiting max %s or use size arg' % (
                        k, len(k), size))

        self._StrSelection = type('StrSelection', (StrSelection,),
                                  {'selections': self.selections})

    def get_col_spec(self):
        return "VARCHAR(%r)" % self.size

    @property
    def python_type(self):
        return self._StrSelection


@Declarations.target_registry(Declarations.Column)
class Selection(Declarations.Column):
    """ Selection column

    ::

        from AnyBlok.declarations import Declarations


        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Selection = Declarations.Selection

        @target_registry(Model)
        class Test:
            STATUS = (
                (u'draft', u'Draft'),
                (u'done', u'Done'),
            )

            x = Selection(selections=STATUS, size=64, default=u'draft')

    """
    def __init__(self, *args, **kwargs):
        selections = tuple()
        size = 64
        if 'selections' in kwargs:
            selections = kwargs.pop('selections')

        if 'size' in kwargs:
            size = kwargs.pop('size')

        self.sqlalchemy_type = SelectionType(selections, size)

        super(Selection, self).__init__(*args, **kwargs)

    def update_properties(self, registry, namespace, fieldname, properties):
        field = properties[fieldname]
        if '_' + fieldname in properties.keys():
            raise Exception('Exception')

        properties['_' + fieldname] = field

        def selection_get(model_self):
            return self.sqlalchemy_type.python_type(
                getattr(model_self, '_' + fieldname))

        def selection_set(model_self, value):
            val = self.sqlalchemy_type.python_type(value)
            if not val.validate():
                raise FieldException('%r is not in the selections (%s)' % (
                    value, ', '.join(val.selections)))

            setattr(model_self, '_' + fieldname, value)

        properties[fieldname] = hybrid_property(selection_get, selection_set)
