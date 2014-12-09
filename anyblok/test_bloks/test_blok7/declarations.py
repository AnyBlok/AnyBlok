from anyblok import Declarations


target_registry = Declarations.target_registry
Model = Declarations.Model
Integer = Declarations.Column.Integer
String = Declarations.Column.String


@target_registry(Model)
class Test:

    id = Integer(primary_key=True)
    label = String()


@target_registry(Model)
class Test2:

    id = Integer(primary_key=True)
    label = String()
