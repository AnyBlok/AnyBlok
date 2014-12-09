from anyblok.tests.testcase import TestCase
from anyblok import Declarations
Field = Declarations.Field
Column = Declarations.Column
RelationShip = Declarations.RelationShip
target_registry = Declarations.target_registry
remove_registry = Declarations.remove_registry
FieldException = Declarations.Exception.FieldException


class OneInterface:
    pass


class TestCoreInterfaceException(TestCase):

    def test_add_interface(self):
        target_registry(Declarations.Exception, cls_=OneInterface,
                        name_='OneException')
        self.assertEqual(
            'Exception',
            Declarations.Exception.OneException.__declaration_type__)
        dir(Declarations.Exception.OneException)

    def test_add_interface_with_decorator(self):

        @target_registry(Declarations.Exception)
        class OneDecoratorException:
            pass

        self.assertEqual(
            'Exception',
            Declarations.Exception.OneDecoratorException.__declaration_type__)
        dir(Declarations.Exception.OneDecoratorException)

    def test_add_same_interface(self):

        target_registry(Declarations.Exception, cls_=OneInterface,
                        name_="SameException")

        try:
            @target_registry(Declarations.Exception)
            class SameException:
                pass

            self.fail('No watch dog to add 2 same field')
        except Declarations.Exception.DeclarationsException:
            pass

    def test_remove_interface(self):

        target_registry(Declarations.Exception, cls_=OneInterface,
                        name_="Exception2Remove")
        try:
            remove_registry(Declarations.Exception.Exception2Remove,
                            OneInterface)
            self.fail('No watch dog to remove field')
        except Declarations.Exception.DeclarationsException:
            pass
