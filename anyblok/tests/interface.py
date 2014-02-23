# -*- coding: utf-8 -*-
import unittest
import AnyBlok
from AnyBlok import target_registry, remove_registry
from AnyBlok import Interface, Core, Field
from AnyBlok.Interface import ICoreInterface
from anyblok.interface import CoreInterfaceException
from anyblok.registry import RegistryManager
from anyblok.field import FieldException


class OneInterface:
    pass

class OneField(Field):
    pass


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
        self.assertEqual(field.get_sqlalchemy_mapping(None, None, None), field)

    def test_add_interface(self):
        target_registry(Field, cls_=OneField, name='OneField')
        self.assertEqual('Field', Field.OneField.__interface__)
        import AnyBlok.Field.OneField
        dir(AnyBlok.Field.OneField)
        self.assertEqual(Field.OneField.is_sql_field(), False)

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
