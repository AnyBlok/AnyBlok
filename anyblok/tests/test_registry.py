# -*- coding: utf-8 -*-
from .anybloktestcase import AnyBlokTestCase
from anyblok.registry import RegistryManager, Registry
from anyblok.blok import BlokManager
from anyblok._argsparse import ArgsParseManager
from anyblok import AnyBlok


old_loaded_bloks = RegistryManager.loaded_bloks
old_declared_entries = []
old_declared_entries += RegistryManager.declared_entries
old_mustbeload_declared_entries = []
old_mustbeload_declared_entries += RegistryManager.mustbeload_declared_entries
old_callback_declared_entries = RegistryManager.callback_declared_entries


class TestRegistryManager(AnyBlokTestCase):

    def setUp(self):
        super(TestRegistryManager, self).setUp()
        RegistryManager.loaded_bloks = old_loaded_bloks.copy()
        RegistryManager.declared_entries = [] + old_declared_entries
        mde = [] + old_mustbeload_declared_entries
        RegistryManager.mustbeload_declared_entries = mde
        cde = old_callback_declared_entries.copy()
        RegistryManager.callback_declared_entries = cde

    def test_declared_entries(self):
        self.assertEqual(RegistryManager.declared_entries, ['Model', 'Mixin'])
        self.assertEqual(RegistryManager.mustbeload_declared_entries,
                         ['Model'])

    def test_init_blok(self):
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        self.assertEqual(RegistryManager.loaded_bloks['newblok'],
                         {
                             'Core': {
                                 'Base': [],
                                 'SqlBase': [],
                                 'Session': [],
                             },
                             'Model': {'registry_names': []},
                             'Mixin': {'registry_names': []}})

    def test_init_blok_with_other_entry(self):
        RegistryManager.declare_entry('Other')
        self.assertEqual(RegistryManager.declared_entries,
                         ['Model', 'Mixin', 'Other'])
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        self.assertEqual(RegistryManager.loaded_bloks['newblok'],
                         {
                             'Core': {
                                 'Base': [],
                                 'SqlBase': [],
                                 'Session': [],
                             },
                             'Model': {'registry_names': []},
                             'Mixin': {'registry_names': []},
                             'Other': {'registry_names': []}})

    def test_anyblok_core_loaded(self):
        BlokManager.load('AnyBlok')
        is_exist = 'anyblok-core' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        anyblokcore = RegistryManager.loaded_bloks['anyblok-core']
        self.assertEqual(len(anyblokcore['Core']['Base']), 1)
        self.assertEqual(len(anyblokcore['Core']['SqlBase']), 1)
        self.assertEqual(len(anyblokcore['Core']['Session']), 1)
        is_exist = 'AnyBlok.Model.System' in anyblokcore['Model']
        self.assertEqual(is_exist, True)
        BlokManager.unload()

    def test_add_mustbeload(self):
        RegistryManager.declare_entry('Other', mustbeload=True)
        self.assertEqual(RegistryManager.declared_entries,
                         ['Model', 'Mixin', 'Other'])
        self.assertEqual(RegistryManager.mustbeload_declared_entries,
                         ['Model', 'Other'])
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        self.assertEqual(RegistryManager.loaded_bloks['newblok'],
                         {
                             'Core': {
                                 'Base': [],
                                 'SqlBase': [],
                                 'Session': [],
                             },
                             'Model': {'registry_names': []},
                             'Mixin': {'registry_names': []},
                             'Other': {'registry_names': []}})

    def test_add_callback(self):

        def callback():
            pass

        RegistryManager.declare_entry('Other', callback=callback)
        self.assertEqual(RegistryManager.declared_entries,
                         ['Model', 'Mixin', 'Other'])
        self.assertEqual(RegistryManager.mustbeload_declared_entries,
                         ['Model'])
        self.assertEqual(RegistryManager.callback_declared_entries,
                         {'Other': callback})
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        self.assertEqual(RegistryManager.loaded_bloks['newblok'],
                         {
                             'Core': {
                                 'Base': [],
                                 'SqlBase': [],
                                 'Session': [],
                             },
                             'Model': {'registry_names': []},
                             'Mixin': {'registry_names': []},
                             'Other': {'registry_names': []}})

    def test_reload_blok(self):
        BlokManager.load('AnyBlok')
        try:
            RegistryManager.reload('anyblok-core')
        finally:
            BlokManager.unload()


class TestRegistryCore(AnyBlokTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegistryCore, cls).setUpClass()
        RegistryManager.init_blok('testCore')
        AnyBlok.current_blok = 'testCore'

    @classmethod
    def tearDownClass(cls):
        super(TestRegistryCore, cls).tearDownClass()
        AnyBlok.current_blok = None
        del RegistryManager.loaded_bloks['testCore']

    def setUp(self):
        super(TestRegistryCore, self).setUp()
        blokname = 'testCore'
        RegistryManager.loaded_bloks[blokname]['Core']['test'] = []

    def assertInCore(self, *args):
        blokname = 'testCore'
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Core']['test']), len(args))
        for cls_ in args:
            hasCls = cls_ in blok['Core']['test']
            self.assertEqual(hasCls, True)

    def test_add_core(self):
        class test:
            pass

        RegistryManager.add_core_in_target_registry('test', test)
        self.assertInCore(test)
        self.assertEqual(
            RegistryManager.has_core_in_target_registry('testCore', 'test'),
            True)

    def test_remove_core(self):
        class test:
            pass

        RegistryManager.add_core_in_target_registry('test', test)
        self.assertInCore(test)
        self.assertEqual(
            RegistryManager.has_core_in_target_registry('testCore', 'test'),
            True)
        RegistryManager.remove_core_in_target_registry(
            'testCore', 'test', test)
        self.assertEqual(
            RegistryManager.has_core_in_target_registry('testCore', 'test'),
            False)


class TestRegistryEntry(AnyBlokTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegistryEntry, cls).setUpClass()
        RegistryManager.declare_entry('Other')
        RegistryManager.init_blok('testEntry')
        AnyBlok.current_blok = 'testEntry'

    @classmethod
    def tearDownClass(cls):
        super(TestRegistryEntry, cls).tearDownClass()
        AnyBlok.current_blok = None
        del RegistryManager.loaded_bloks['testEntry']

    def tearDown(self):
        super(TestRegistryEntry, self).tearDown()
        del RegistryManager.loaded_bloks['testEntry']['Other']['test']

    def assertInEntry(self, entry, *args):
        blokname = 'testEntry'
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Other'][entry]['bases']), len(args))
        for cls_ in args:
            hasCls = cls_ in blok['Other'][entry]['bases']
            self.assertEqual(hasCls, True)

    def test_add_core(self):
        class test:
            pass

        RegistryManager.add_entry_in_target_registry('Other', 'test', test)
        self.assertInEntry('test', test)
        self.assertEqual(
            RegistryManager.has_entry_in_target_registry('testEntry', 'Other',
                                                         'test'),
            True)

    def test_remove_core(self):
        class test:
            pass

        RegistryManager.add_entry_in_target_registry('Other', 'test', test)
        self.assertInEntry('test', test)
        self.assertEqual(
            RegistryManager.has_entry_in_target_registry('testEntry', 'Other',
                                                         'test'),
            True)
        RegistryManager.remove_entry_in_target_registry(
            'testEntry', 'Other', 'test', test)
        self.assertEqual(
            RegistryManager.has_entry_in_target_registry('testEntry', 'Other',
                                                         'test'),
            False)


class TestRegistry(AnyBlokTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegistry, cls).setUpClass()
        env = {
            'dbname': '',
            'dbdrivername': 'sqlite',
            'dbusername': '',
            'dbpassword': '',
            'dbhost': '',
            'dbport': '',
        }
        ArgsParseManager.configuration = env
        BlokManager.load('AnyBlok')

    def setUp(self):
        super(TestRegistry, self).setUp()
        self.registry = Registry(':memory:')

    @classmethod
    def tearDownClass(cls):
        super(TestRegistry, cls).tearDownClass()
        BlokManager.unload()

    def tearDown(self):
        super(TestRegistry, self).tearDown()
        RegistryManager.clear()

    def test_get(self):
        self.registry.close()
        self.registry = RegistryManager.get(':memory:')

    def test_get_model(self):
        System = self.registry.get('AnyBlok.Model.System')
        self.assertEqual(self.registry.System, System)

    def test_get_the_same_registry(self):
        self.registry.close()
        registry1 = RegistryManager.get(':memory:')
        registry2 = RegistryManager.get(':memory:')
        self.assertEqual(registry1, registry2)

    def test_get_the_same_registry_after_reload(self):
        bloks_before_reload = self.registry.System.Blok.query('name').filter(
            self.registry.System.Blok.state == 'installed').all()
        RegistryManager.reload('anyblok-core')
        bloks_after_reload = self.registry.System.Blok.query('name').filter(
            self.registry.System.Blok.state == 'installed').all()
        self.assertEqual(bloks_before_reload, bloks_after_reload)

    def test_reload(self):
        bloks_before_reload = self.registry.System.Blok.query('name').filter(
            self.registry.System.Blok.state == 'installed').all()
        self.registry.reload()
        bloks_after_reload = self.registry.System.Blok.query('name').filter(
            self.registry.System.Blok.state == 'installed').all()
        self.assertEqual(bloks_before_reload, bloks_after_reload)
