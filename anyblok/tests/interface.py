# -*- coding: utf-8 -*-
import unittest
from anyblok import AnyBlok
from anyblok.interface import CoreInterfaceException
from anyblok.registry import RegistryManager


class OneInterface:
    pass


class TestCoreInterface(unittest.TestCase):

    def test_add_interface(self):

        AnyBlok.target_registry(AnyBlok.Interface, cls_=OneInterface)
        self.assertEqual(OneInterface, AnyBlok.Interface.OneInterface)
        self.assertEqual(
            'Interface', AnyBlok.Interface.OneInterface.__interface__)

    def test_add_interface_with_name(self):

        AnyBlok.target_registry(AnyBlok.Interface, cls_=OneInterface,
                                name='OtherClsName')
        self.assertEqual(OneInterface, AnyBlok.Interface.OtherClsName)
        self.assertEqual(
            'Interface', AnyBlok.Interface.OtherClsName.__interface__)

    def test_add_interface_with_decorator(self):

        @AnyBlok.target_registry(AnyBlok.Interface)
        class OtherInterface:
            pass

        self.assertEqual(OtherInterface, AnyBlok.Interface.OtherInterface)
        self.assertEqual(
            'Interface', AnyBlok.Interface.OtherInterface.__interface__)

    def test_add_interface_doublon(self):

        AnyBlok.target_registry(AnyBlok.Interface, cls_=OneInterface,
                                name="InterfaceDoublon")
        try:
            AnyBlok.target_registry(AnyBlok.Interface, cls_=OneInterface,
                                    name="InterfaceDoublon")
            self.fail(
                "No exception when we put more than 1 time one interface")
        except CoreInterfaceException:
            pass

    def test_remove_interface(self):

        AnyBlok.target_registry(AnyBlok.Interface, cls_=OneInterface,
                                name="InterfaceToRemove")
        AnyBlok.remove_registry(AnyBlok.Interface, cls_=OneInterface,
                                name="InterfaceToRemove")
        self.assertEqual(hasattr(AnyBlok.Interface, "InterfaceToRemove"),
                         False)


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

    def test_add_interface(self):
        AnyBlok.target_registry(AnyBlok.Core, cls_=OneInterface,
                                name='Base')
        self.assertEqual('Core', AnyBlok.Core.Base.__interface__)
        self.assertInCore(OneInterface)

    def test_add_interface_with_decorator(self):

        @AnyBlok.target_registry(AnyBlok.Core)
        class Base:
            pass

        self.assertEqual('Core', AnyBlok.Core.Base.__interface__)
        self.assertInCore(Base)

    def test_add_two_interface(self):

        AnyBlok.target_registry(AnyBlok.Core, cls_=OneInterface,
                                name="Base")

        @AnyBlok.target_registry(AnyBlok.Core)
        class Base:
            pass

        self.assertInCore(OneInterface, Base)

    def test_remove_interface_with_1_cls_in_registry(self):

        AnyBlok.target_registry(AnyBlok.Core, cls_=OneInterface,
                                name="Base")

        self.assertInCore(OneInterface)

        blokname = 'testCore' + self._corename
        AnyBlok.remove_registry(AnyBlok.Core, cls_=OneInterface,
                                name="Base", blok=blokname)

        blokname = 'testCore' + self._corename
        self.assertEqual(hasattr(AnyBlok.Core, blokname), False)
        self.assertInCore()

    def test_remove_interface_with_2_cls_in_registry(self):

        AnyBlok.target_registry(AnyBlok.Core, cls_=OneInterface,
                                name="Base")

        @AnyBlok.target_registry(AnyBlok.Core)
        class Base:
            pass

        self.assertInCore(OneInterface, Base)

        blokname = 'testCore' + self._corename
        AnyBlok.remove_registry(AnyBlok.Core, cls_=OneInterface,
                                name="Base", blok=blokname)

        self.assertInCore(Base)
