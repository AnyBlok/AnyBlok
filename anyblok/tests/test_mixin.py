from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok import Declarations
from anyblok.environment import EnvironmentManager
target_registry = Declarations.target_registry
remove_registry = Declarations.remove_registry
Mixin = Declarations.Mixin


class OneInterface:
    pass


class TestCoreInterfaceMixin(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCoreInterfaceMixin, cls).setUpClass()
        RegistryManager.init_blok('testMixin')
        EnvironmentManager.set('current_blok', 'testMixin')

    @classmethod
    def tearDownClass(cls):
        super(TestCoreInterfaceMixin, cls).tearDownClass()
        EnvironmentManager.set('current_blok', None)
        del RegistryManager.loaded_bloks['testMixin']

    def setUp(self):
        super(TestCoreInterfaceMixin, self).setUp()
        blokname = 'testMixin'
        RegistryManager.loaded_bloks[blokname]['Mixin'] = {
            'registry_names': []}

    def assertInMixin(self, *args):
        blokname = 'testMixin'
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Mixin']['Mixin.MyMixin']['bases']),
                         len(args))
        for cls_ in args:
            has = cls_ in blok['Mixin']['Mixin.MyMixin']['bases']
            self.assertEqual(has, True)

    def assertInRemoved(self, cls):
        core = RegistryManager.loaded_bloks['testMixin']['removed']
        if cls in core:
            return True

        self.fail('Not in removed')

    def test_add_interface(self):
        target_registry(Mixin, cls_=OneInterface, name_='MyMixin')
        self.assertEqual('Mixin', Mixin.MyMixin.__declaration_type__)
        self.assertInMixin(OneInterface)
        dir(Declarations.Mixin.MyMixin)

    def test_add_interface_with_decorator(self):

        @target_registry(Mixin)
        class MyMixin:
            pass

        self.assertEqual('Mixin', Mixin.MyMixin.__declaration_type__)
        self.assertInMixin(MyMixin)

    def test_add_two_interface(self):

        target_registry(Mixin, cls_=OneInterface, name_="MyMixin")

        @target_registry(Mixin)
        class MyMixin:
            pass

        self.assertInMixin(OneInterface, MyMixin)

    def test_remove_interface_with_1_cls_in_registry(self):

        target_registry(Mixin, cls_=OneInterface, name_="MyMixin")
        self.assertInMixin(OneInterface)
        remove_registry(Mixin.MyMixin, OneInterface)

        blokname = 'testMixin'
        self.assertEqual(hasattr(Mixin, blokname), False)
        self.assertInMixin(OneInterface)
        self.assertInRemoved(OneInterface)

    def test_remove_interface_with_2_cls_in_registry(self):

        target_registry(Mixin, cls_=OneInterface, name_="MyMixin")

        @target_registry(Mixin)
        class MyMixin:
            pass

        self.assertInMixin(OneInterface, MyMixin)
        remove_registry(Mixin.MyMixin, OneInterface)
        self.assertInMixin(MyMixin, OneInterface)
        self.assertInRemoved(OneInterface)
