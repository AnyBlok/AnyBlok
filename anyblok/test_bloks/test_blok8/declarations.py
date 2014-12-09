from anyblok import Declarations


target_registry = Declarations.target_registry
Model = Declarations.Model
Integer = Declarations.Column.Integer
String = Declarations.Column.String


@target_registry(Model)
class Test:

    test2 = Integer(foreign_key=(Model.Test2, 'id'))
