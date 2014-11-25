from anyblok.tests.testcase import BlokTestCase, DBTestCase


class TestSystemBlok(BlokTestCase):

    def test_list_by_state_installed(self):
        installed = self.registry.System.Blok.list_by_state('installed')
        core_is_installed = 'anyblok-core' in installed
        self.assertEqual(core_is_installed, True)

    def test_list_by_state_without_state(self):
        self.assertEqual(self.registry.System.Blok.list_by_state(), None)


class TestBlok1(DBTestCase):

    parts_to_load = ['AnyBlok', 'TestAnyBlok']

    def test_blok_exist(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok1')
        if not query.count():
            self.fail('No blok found')

        testblok1 = query.first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok1.short_description, '')
        self.assertEqual(testblok1.long_description, '')

    def test_install(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')

    def test_uninstall(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        self.upgrade(registry, uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)

    def test_update(self):
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


class TestBlok2(DBTestCase):

    parts_to_load = ['AnyBlok', 'TestAnyBlok']

    def test_blok_exist(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok2')
        if not query.count():
            self.fail('No blok found')

        testblok2 = query.first()
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.assertEqual(testblok2.short_description, 'Test blok2')

    def test_install_1by1(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.upgrade(registry, install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')

    def test_install(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        self.upgrade(registry, install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')

    def test_uninstall(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok2',))
        self.upgrade(registry, uninstall=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)

    def test_uninstall_required(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok2',))
        self.upgrade(registry, uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)

    def test_update(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        self.upgrade(registry, update=('test-blok2',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '2.0.0')

    def test_update_required(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        self.upgrade(registry, update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '2.0.0')
