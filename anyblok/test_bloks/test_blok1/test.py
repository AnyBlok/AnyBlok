from anyblok import Declarations


target_registry = Declarations.target_registry
Model = Declarations.Model
Integer = Declarations.Column.Integer
String = Declarations.Column.String


@target_registry(Model)
class Test:

    id = Integer(primary_key=True)
    blok = String()
    mode = String()


@target_registry(Model.System)
class Blok:

    def install(self):
        super(Blok, self).upgrade()
        self.registry.Test.insert(blok=self.name, mode='install')

    def upgrade(self):
        super(Blok, self).upgrade()
        self.registry.Test.insert(blok=self.name, mode='update')

    def load(self):
        super(Blok, self).load()
        self.registry.Test.insert(blok=self.name, mode='load')
