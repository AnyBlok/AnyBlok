from anyblok.tests.testcase import BlokTestCase, DBTestCase


class TestSystemBlok(BlokTestCase):

    def test_list_by_state_installed(self):
        installed = self.registry.System.Blok.list_by_state('installed')
        core_is_installed = 'anyblok-core' in installed
        self.assertEqual(core_is_installed, True)

    def test_list_by_state_without_state(self):
        self.assertEqual(self.registry.System.Blok.list_by_state(), None)


class TestSystemBlokManagement(DBTestCase):

    parts_to_load = ['AnyBlok', 'TestAnyBlok']

    def test_blok1(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok1')
        if not query.count():
            self.fail('No blok found')

        testblok1 = query.first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)

    def test_blok1_install(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')

    def test_blok1_uninstall(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        self.upgrade(registry, uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)

    def test_blok1_update(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok1.version = '2.0.0'
        self.upgrade(registry, update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
