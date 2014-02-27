# -*- coding: utf-8 -*-
import unittest
import AnyBlok
from AnyBlok import target_registry, remove_registry
from AnyBlok import Interface, Core, Field, Column, RelationShip, Mixin, Model
from anyblok.interface import CoreInterfaceException
from anyblok.registry import RegistryManager
from anyblok.field import FieldException
from sqlalchemy import Integer as SA_Integer


class OneInterface:
    pass


class OneField(Field):
    pass


class OneColumn(Column):
    sqlalchemy_type = SA_Integer


class OneRelationShip(RelationShip):
    pass


class OneModel:
    __tablename__ = 'test'


class TestCoreInterface(unittest.TestCase):

    def test_add_interface(self):

        target_registry(Interface, cls_=OneInterface)
        self.assertEqual(OneInterface, Interface.OneInterface)
        self.assertEqual('Interface', Interface.OneInterface.__interface__)
        import AnyBlok.Interface.OneInterface
        dir(AnyBlok.Interface.OneInterface)

    def test_add_interface_with_name(self):

        target_registry(Interface, cls_=OneInterface, name='OtherClsName')
        self.assertEqual(OneInterface, Interface.OtherClsName)
        self.assertEqual('Interface', Interface.OtherClsName.__interface__)
        import AnyBlok.Interface.OtherClsName
        dir(AnyBlok.Interface.OtherClsName)

    def test_add_tree_interface(self):
        target_registry(Interface, cls_=OneInterface, name="ITree1")
        try:
            target_registry(Interface.ITree1, cls_=OneInterface, name="ITree2")
            self.fail("No watchdog for tree interface")
        except CoreInterfaceException:
            pass

    def test_add_interface_with_decorator(self):

        @target_registry(Interface)
        class OtherInterface:
            pass

        self.assertEqual(OtherInterface, Interface.OtherInterface)
        self.assertEqual('Interface', Interface.OtherInterface.__interface__)

    def test_add_interface_doublon(self):

        target_registry(Interface, cls_=OneInterface, name="InterfaceDoublon")
        try:
            target_registry(Interface, cls_=OneInterface,
                            name="InterfaceDoublon")
            self.fail(
                "No exception when we put more than 1 time one interface")
        except CoreInterfaceException:
            pass

    def test_remove_interface(self):

        target_registry(Interface, cls_=OneInterface, name="InterfaceToRemove")
        remove_registry(Interface, cls_=OneInterface, name="InterfaceToRemove")
        self.assertEqual(hasattr(Interface, "InterfaceToRemove"), False)


class TestCoreInterfaceCoreBase(unittest.TestCase):

    _corename = 'Base'

    @classmethod
    def setUpClass(cls):
        super(TestCoreInterfaceCoreBase, cls).setUpClass()
        RegistryManager.init_blok('testCore' + cls._corename)
        AnyBlok.current_blok = 'testCore' + cls._corename

    @classmethod
    def tearDownClass(cls):
        super(TestCoreInterfaceCoreBase, cls).tearDownClass()
        AnyBlok.current_blok = None
        del RegistryManager.loaded_bloks['testCore' + cls._corename]

    def setUp(self):
        super(TestCoreInterfaceCoreBase, self).setUp()
        blokname = 'testCore' + self._corename
        RegistryManager.loaded_bloks[blokname]['Core'][self._corename] = []

    def assertInCore(self, *args):
        blokname = 'testCore' + self._corename
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Core'][self._corename]), len(args))
        for cls_ in args:
            hasCls = cls_ in blok['Core'][self._corename]
            self.assertEqual(hasCls, True)

    def test_import_Interface1(self):
        import AnyBlok.Interface.ICoreInterface
        dir(AnyBlok.Interface.ICoreInterface)

    def test_add_interface(self):
        target_registry(Core, cls_=OneInterface, name='Base')
        self.assertEqual('Core', Core.Base.__interface__)
        self.assertInCore(OneInterface)
        import AnyBlok.Core.Base
        dir(AnyBlok.Core.Base)

    def test_add_interface_with_decorator(self):

        @target_registry(Core)
        class Base:
            pass

        self.assertEqual('Core', Core.Base.__interface__)
        self.assertInCore(Base)

    def test_add_two_interface(self):

        target_registry(Core, cls_=OneInterface, name="Base")

        @target_registry(Core)
        class Base:
            pass

        self.assertInCore(OneInterface, Base)

    def test_remove_interface_with_1_cls_in_registry(self):

        target_registry(Core, cls_=OneInterface, name="Base")
        self.assertInCore(OneInterface)
        blokname = 'testCore' + self._corename
        remove_registry(Core, cls_=OneInterface, name="Base", blok=blokname)

        blokname = 'testCore' + self._corename
        self.assertEqual(hasattr(Core, blokname), False)
        self.assertInCore()

    def test_remove_interface_with_2_cls_in_registry(self):

        target_registry(Core, cls_=OneInterface, name="Base")

        @target_registry(Core)
        class Base:
            pass

        self.assertInCore(OneInterface, Base)
        blokname = 'testCore' + self._corename
        remove_registry(Core, cls_=OneInterface, name="Base", blok=blokname)
        self.assertInCore(Base)


class TestCoreInterfaceField(unittest.TestCase):

    def test_import_Field(self):
        import AnyBlok.Field
        dir(AnyBlok.Field)

    def test_MustNotBeInstanced(self):
        try:
            Field(label="Test")
            self.fail("Field mustn't be instanced")
        except FieldException:
            pass

    def test_must_have_label(self):
        target_registry(Field, cls_=OneField, name='RealField')
        field = Field.RealField(label='test')
        try:
            Field.RealField()
            self.fail("No watchdog, the label must be required")
        except FieldException:
            pass
        self.assertEqual(field.get_sqlalchemy_mapping(None, None, None, None),
                         field)

    def test_add_interface(self):
        target_registry(Field, cls_=OneField, name='OneField')
        self.assertEqual('Field', Field.OneField.__interface__)
        import AnyBlok.Field.OneField
        dir(AnyBlok.Field.OneField)

    def test_add_interface_with_decorator(self):

        @target_registry(Field)
        class OneDecoratorField(OneField):
            pass

        self.assertEqual('Field', Field.OneDecoratorField.__interface__)
        import AnyBlok.Field.OneDecoratorField
        dir(AnyBlok.Field.OneDecoratorField)

    def test_add_same_interface(self):

        target_registry(Field, cls_=OneField, name="SameField")

        try:
            @target_registry(Field)
            class SameField(OneField):
                pass

            self.fail('No watch dog to add 2 same field')
        except FieldException:
            pass

    def test_remove_interface(self):

        target_registry(Field, cls_=OneField, name="Field2Remove")
        try:
            remove_registry(Field, cls_=OneField, name="Field2Remove")
            self.fail('No watch dog to remove field')
        except FieldException:
            pass


class TestCoreInterfaceColumn(unittest.TestCase):

    def test_import_Column(self):
        import AnyBlok.Column
        dir(AnyBlok.Column)

    def test_MustNotBeInstanced(self):
        try:
            Column(label="Test")
            self.fail("Column mustn't be instanced")
        except FieldException:
            pass

    def test_must_have_label(self):
        target_registry(Column, cls_=OneColumn, name='RealColumn')
        Column.RealColumn(label='test')
        try:
            Column.RealColumn()
            self.fail("No watchdog, the label must be required")
        except FieldException:
            pass

    def test_add_interface(self):
        target_registry(Column, cls_=OneColumn, name='OneColumn')
        self.assertEqual('Column', Column.OneColumn.__interface__)
        import AnyBlok.Column.OneColumn
        dir(AnyBlok.Column.OneColumn)

    def test_add_interface_with_decorator(self):

        @target_registry(Column)
        class OneDecoratorColumn(Column):
            sqlalchemy_type = SA_Integer

        self.assertEqual('Column', Column.OneDecoratorColumn.__interface__)
        import AnyBlok.Column.OneDecoratorColumn
        dir(AnyBlok.Column.OneDecoratorColumn)

    def test_add_same_interface(self):

        target_registry(Field, cls_=OneColumn, name="SameColumn")

        try:
            @target_registry(Column)
            class SameColumn(Column):
                sqlalchemy_type = SA_Integer

            self.fail('No watch dog to add 2 same Column')
        except FieldException:
            pass

    def test_remove_interface(self):

        target_registry(Field, cls_=OneField, name="Column2Remove")
        try:
            remove_registry(Field, cls_=OneField, name="Column2Remove")
            self.fail('No watch dog to remove Column')
        except FieldException:
            pass


class TestCoreInterfaceRelationShip(unittest.TestCase):

    def test_import_RelationShip(self):
        import AnyBlok.RelationShip
        dir(AnyBlok.RelationShip)

    def test_MustNotBeInstanced(self):
        try:
            RelationShip(label="Test", model=OneModel)
            self.fail("RelationShip mustn't be instanced")
        except FieldException:
            pass

    def test_must_have_label_and_model(self):
        target_registry(RelationShip, cls_=OneRelationShip,
                        name="RealRelationShip")
        RelationShip.RealRelationShip(label='test', model=OneModel)
        try:
            RelationShip.RealRelationShip(model=OneModel)
            self.fail("No watchdog, the label must be required")
        except FieldException:
            pass
        try:
            RelationShip.RealRelationShip(label="test")
            self.fail("No watchdog, the model must be required")
        except FieldException:
            pass

    def test_add_interface(self):
        target_registry(RelationShip, cls_=OneRelationShip)
        self.assertEqual('RelationShip',
                         RelationShip.OneRelationShip.__interface__)
        import AnyBlok.RelationShip.OneRelationShip
        dir(AnyBlok.RelationShip.OneRelationShip)

    def test_add_interface_with_decorator(self):

        @target_registry(RelationShip)
        class OneDecoratorRelationShip(RelationShip):
            pass

        self.assertEqual('RelationShip',
                         RelationShip.OneDecoratorRelationShip.__interface__)
        import AnyBlok.RelationShip.OneDecoratorRelationShip
        dir(AnyBlok.RelationShip.OneDecoratorRelationShip)

    def test_add_same_interface(self):

        target_registry(RelationShip, cls_=OneRelationShip,
                        name="SameRelationShip")

        try:
            @target_registry(RelationShip)
            class SameRelationShip(RelationShip):
                pass

            self.fail('No watch dog to add 2 same relation ship')
        except FieldException:
            pass

    def test_remove_interface(self):

        target_registry(RelationShip, cls_=OneRelationShip,
                        name="RelationShip2Remove")
        try:
            remove_registry(RelationShip, cls_=OneRelationShip,
                            name="RelationShip2Remove")
            self.fail('No watch dog to remove relation ship')
        except FieldException:
            pass


class TestCoreInterfaceMixin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCoreInterfaceMixin, cls).setUpClass()
        RegistryManager.init_blok('testMixin')
        AnyBlok.current_blok = 'testMixin'

    @classmethod
    def tearDownClass(cls):
        super(TestCoreInterfaceMixin, cls).tearDownClass()
        AnyBlok.current_blok = None
        del RegistryManager.loaded_bloks['testMixin']

    def setUp(self):
        super(TestCoreInterfaceMixin, self).setUp()
        blokname = 'testMixin'
        RegistryManager.loaded_bloks[blokname]['Mixin'] = {
            'registry_names': []}

    def assertInMixin(self, *args):
        blokname = 'testMixin'
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Mixin']['AnyBlok.Mixin.MyMixin']['bases']),
                         len(args))
        for cls_ in args:
            hasCls = cls_ in blok['Mixin']['AnyBlok.Mixin.MyMixin']['bases']
            self.assertEqual(hasCls, True)

    def test_import_Interface1(self):
        import AnyBlok.Mixin
        dir(AnyBlok.Mixin)

    def test_add_interface(self):
        target_registry(Mixin, cls_=OneInterface, name='MyMixin')
        self.assertEqual('Mixin', Mixin.MyMixin.__interface__)
        self.assertInMixin(OneInterface)
        import AnyBlok.Mixin.MyMixin
        dir(AnyBlok.Mixin.MyMixin)

    def test_add_interface_with_decorator(self):

        @target_registry(Mixin)
        class MyMixin:
            pass

        self.assertEqual('Mixin', Mixin.MyMixin.__interface__)
        self.assertInMixin(MyMixin)

    def test_add_two_interface(self):

        target_registry(Mixin, cls_=OneInterface, name="MyMixin")

        @target_registry(Mixin)
        class MyMixin:
            pass

        self.assertInMixin(OneInterface, MyMixin)

    def test_remove_interface_with_1_cls_in_registry(self):

        target_registry(Mixin, cls_=OneInterface, name="MyMixin")
        self.assertInMixin(OneInterface)
        blokname = 'testMixin'
        remove_registry(Mixin, cls_=OneInterface, name="MyMixin",
                        blok=blokname)

        blokname = 'testMixin'
        self.assertEqual(hasattr(Mixin, blokname), False)
        self.assertInMixin()

    def test_remove_interface_with_2_cls_in_registry(self):

        target_registry(Mixin, cls_=OneInterface, name="MyMixin")

        @target_registry(Mixin)
        class MyMixin:
            pass

        self.assertInMixin(OneInterface, MyMixin)
        blokname = 'testMixin'
        remove_registry(Mixin, cls_=OneInterface, name="MyMixin",
                        blok=blokname)
        self.assertInMixin(MyMixin)


class TestCoreInterfaceModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCoreInterfaceModel, cls).setUpClass()
        RegistryManager.init_blok('testModel')
        AnyBlok.current_blok = 'testModel'

    @classmethod
    def tearDownClass(cls):
        super(TestCoreInterfaceModel, cls).tearDownClass()
        AnyBlok.current_blok = None
        del RegistryManager.loaded_bloks['testModel']

    def setUp(self):
        super(TestCoreInterfaceModel, self).setUp()
        blokname = 'testModel'
        RegistryManager.loaded_bloks[blokname]['Model'] = {
            'registry_names': []}

    def assertInModel(self, *args):
        blokname = 'testModel'
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Model']['AnyBlok.Model.MyModel']['bases']),
                         len(args))
        for cls_ in args:
            hasCls = cls_ in blok['Model']['AnyBlok.Model.MyModel']['bases']
            self.assertEqual(hasCls, True)

    def test_import_Interface1(self):
        import AnyBlok.Model
        dir(AnyBlok.Model)

    def test_add_interface(self):
        target_registry(Model, cls_=OneInterface, name='MyModel')
        self.assertEqual('Model', Model.MyModel.__interface__)
        self.assertInModel(OneInterface)
        import AnyBlok.Model.MyModel
        dir(AnyBlok.Model.MyModel)

    def test_add_interface_with_decorator(self):

        @target_registry(Model)
        class MyModel:
            pass

        self.assertEqual('Model', Model.MyModel.__interface__)
        self.assertInModel(MyModel)

    def test_add_two_interface(self):

        target_registry(Model, cls_=OneInterface, name="MyModel")

        @target_registry(Model)
        class MyModel:
            pass

        self.assertInModel(OneInterface, MyModel)

    def test_remove_interface_with_1_cls_in_registry(self):

        target_registry(Model, cls_=OneInterface, name="MyModel")
        self.assertInModel(OneInterface)
        blokname = 'testModel'
        remove_registry(Model, cls_=OneInterface, name="MyModel",
                        blok=blokname)

        blokname = 'testModel'
        self.assertEqual(hasattr(Model, blokname), False)
        self.assertInModel()

    def test_remove_interface_with_2_cls_in_registry(self):

        target_registry(Model, cls_=OneInterface, name="MyModel")

        @target_registry(Model)
        class MyModel:
            pass

        self.assertInModel(OneInterface, MyModel)
        blokname = 'testModel'
        remove_registry(Model, cls_=OneInterface, name="MyModel",
                        blok=blokname)
        self.assertInModel(MyModel)
