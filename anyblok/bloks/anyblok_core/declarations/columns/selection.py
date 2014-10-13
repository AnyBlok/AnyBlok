from anyblok import Declarations
from sqlalchemy import types


class StrSelection(str):
    selections = {}

    #def __eq__(self, other):
    #    return other == self

    #def __ne__(self, other):
    #    return not (self == other)

    def __str__(self):
        a = super(StrSelection, self).__str__()
        return dict(self.selections)[a]

    def __repr__(self):
        a = super(StrSelection, self).__str__()
        b = self.selections[a]
        return "Selection : %s(%r)" % (b, a)


class SelectionType(types.UserDefinedType):

    def __init__(self, selections, size):
        super(SelectionType, self).__init__()
        self.size = size
        if isinstance(selections, dict):
            self.selections = selections
        elif isinstance(selections, (list, tuple)):
            self.selections = dict(selections)
        else:
            raise Exception('Bad value')

        for k in self.selections.keys():
            if len(k) > 64:
                raise Exception('taille trop grande')

        self._StrSelection = type('StrSelection', (StrSelection,),
                                  {'selections': self.selections})

    def get_col_spec(self):
        return "VARCHAR(%r)" % self.size

    def bind_processor(self, dialect):
        def process(value):
            if value in self.selections.keys():
                #if not isinstance(value, self._StrSelection):
                #    value = self._StrSelection(value)

                return value
            else:
                raise Exception('Bad value 2')

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return self._StrSelection(value)

        return process

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
