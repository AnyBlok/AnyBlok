# -*- coding: utf-8 -*-
import unittest
from anyblok import AnyBlok
from anyblok.interface import CoreInterfaceException


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
