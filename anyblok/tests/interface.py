# -*- coding: utf-8 -*-
import unittest
import AnyBlok
from AnyBlok import target_registry, remove_registry
from AnyBlok import Interface, Core
from AnyBlok.Interface import ICoreInterface
from anyblok.interface import CoreInterfaceException
from anyblok.registry import RegistryManager


class OneInterface:
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
