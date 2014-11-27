from anyblok.tests.testcase import BlokTestCase, DBTestCase
from anyblok import Declarations


class TestSystemBlok(BlokTestCase):

    def test_list_by_state_installed(self):
        installed = self.registry.System.Blok.list_by_state('installed')
        core_is_installed = 'anyblok-core' in installed
        self.assertEqual(core_is_installed, True)

    def test_list_by_state_without_state(self):
        self.assertEqual(self.registry.System.Blok.list_by_state(), None)


class TestBlok(DBTestCase):

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

    def test_install_an_installed_blok(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        try:
            self.upgrade(registry, install=('test-blok1',))
            self.fail('No watchdog to install an installed blok')
        except Declarations.Exception.RegistryException:
            pass

    def test_uninstall(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        self.upgrade(registry, uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)

    def test_uninstall_an_uninstalled_blok(self):
        registry = self.init_registry(None)
        try:
            self.upgrade(registry, uninstall=('test-blok1',))
            self.fail('No watchdog to uninstall an uninstalled blok')
        except Declarations.Exception.RegistryException:
            pass

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

    def test_update_an_uninstalled_blok(self):
        registry = self.init_registry(None)
        try:
            self.upgrade(registry, update=('test-blok1',))
            self.fail('No watchdog to update an uninstalled blok')
        except Declarations.Exception.RegistryException:
            pass


class TestBlokRequired(DBTestCase):

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


class TestBlokRequired2(DBTestCase):

    parts_to_load = ['AnyBlok', 'TestAnyBlok']

    def test_blok_exist(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok3')
        if not query.count():
            self.fail('No blok found')

        testblok2 = query.first()
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.assertEqual(testblok2.long_description, 'Test blok3\n')

    def test_install_1by1(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.assertEqual(testblok3.state, 'uninstalled')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, None)
        self.upgrade(registry, install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')
        self.assertEqual(testblok3.state, 'uninstalled')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, None)
        self.upgrade(registry, install=('test-blok3',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')
        self.assertEqual(testblok3.state, 'installed')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, '1.0.0')

    def test_install(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        self.upgrade(registry, install=('test-blok3',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')
        self.assertEqual(testblok3.state, 'installed')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, '1.0.0')

    def test_uninstall(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.upgrade(registry, uninstall=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')
        self.assertEqual(testblok3.state, 'uninstalled')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, None)

    def test_uninstall_first_required(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.upgrade(registry, uninstall=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.assertEqual(testblok3.state, 'uninstalled')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, None)

    def test_uninstall_all_required(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.upgrade(registry, uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.assertEqual(testblok3.state, 'uninstalled')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, None)

    def test_update(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        self.upgrade(registry, update=('test-blok3',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '1.0.0')
        self.assertEqual(testblok3.state, 'installed')
        self.assertEqual(testblok3.installed_version, '2.0.0')

    def test_update_first_required(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        self.upgrade(registry, update=('test-blok2',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '2.0.0')
        self.assertEqual(testblok3.state, 'installed')
        self.assertEqual(testblok3.installed_version, '2.0.0')

    def test_update_all_required(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        self.upgrade(registry, update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '2.0.0')
        self.assertEqual(testblok3.state, 'installed')
        self.assertEqual(testblok3.installed_version, '2.0.0')


class TestBlokConditionnal(DBTestCase):

    parts_to_load = ['AnyBlok', 'TestAnyBlok']

    def test_install_1by1(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok4.state, 'uninstalled')
        self.assertEqual(testblok4.version, '1.0.0')
        self.assertEqual(testblok4.installed_version, None)
        self.assertEqual(testblok5.state, 'uninstalled')
        self.assertEqual(testblok5.version, '1.0.0')
        self.assertEqual(testblok5.installed_version, None)
        self.upgrade(registry, install=('test-blok4',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok4.state, 'installed')
        self.assertEqual(testblok4.version, '1.0.0')
        self.assertEqual(testblok4.installed_version, '1.0.0')
        self.assertEqual(testblok5.state, 'installed')
        self.assertEqual(testblok5.version, '1.0.0')
        self.assertEqual(testblok5.installed_version, '1.0.0')

    def test_install(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        self.upgrade(registry, install=('test-blok5',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok4.state, 'installed')
        self.assertEqual(testblok4.version, '1.0.0')
        self.assertEqual(testblok4.installed_version, '1.0.0')
        self.assertEqual(testblok5.state, 'installed')
        self.assertEqual(testblok5.version, '1.0.0')
        self.assertEqual(testblok5.installed_version, '1.0.0')

    def test_uninstall(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok5',))
        try:
            self.upgrade(registry, uninstall=('test-blok5',))
            self.fail('No watchdog to uninstall conditionnal blok')
        except Declarations.Exception.RegistryException:
            pass

    def test_uninstall_conditionnal(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok5',))
        self.upgrade(registry, uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok4.state, 'installed')
        self.assertEqual(testblok4.version, '1.0.0')
        self.assertEqual(testblok4.installed_version, '1.0.0')
        self.assertEqual(testblok5.state, 'uninstalled')
        self.assertEqual(testblok5.version, '1.0.0')
        self.assertEqual(testblok5.installed_version, None)

    def test_update(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok5',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        testblok1.version = '2.0.0'
        testblok4.version = '2.0.0'
        testblok5.version = '2.0.0'
        self.upgrade(registry, update=('test-blok5',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok4.state, 'installed')
        self.assertEqual(testblok4.installed_version, '1.0.0')
        self.assertEqual(testblok5.state, 'installed')
        self.assertEqual(testblok5.installed_version, '2.0.0')

    def test_update_conditionnal(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok5',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        testblok1.version = '2.0.0'
        testblok4.version = '2.0.0'
        testblok5.version = '2.0.0'
        self.upgrade(registry, update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
        self.assertEqual(testblok4.state, 'installed')
        self.assertEqual(testblok4.installed_version, '1.0.0')
        self.assertEqual(testblok5.state, 'installed')
        self.assertEqual(testblok5.installed_version, '2.0.0')


class TestBlokOptional(DBTestCase):

    parts_to_load = ['AnyBlok', 'TestAnyBlok']

    def test_install_1by1(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'uninstalled')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, None)
        self.upgrade(registry, install=('test-blok6',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, '1.0.0')

    def test_install(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        self.upgrade(registry, install=('test-blok6',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, '1.0.0')

    def test_uninstall(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok6',))
        self.upgrade(registry, uninstall=('test-blok6',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'uninstalled')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, None)

    def test_uninstall_optional(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        self.upgrade(registry, install=('test-blok6',))
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok6.version = '2.0.0'
        self.upgrade(registry, uninstall=('test-blok1',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.version, '2.0.0')
        self.assertEqual(testblok6.installed_version, '2.0.0')

    def test_update(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok6',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok1.version = '2.0.0'
        testblok6.version = '2.0.0'
        self.upgrade(registry, update=('test-blok6',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.installed_version, '2.0.0')

    def test_update_optional(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok6',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok1.version = '2.0.0'
        testblok6.version = '2.0.0'
        self.upgrade(registry, update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.installed_version, '2.0.0')


class TestBlokOrder(DBTestCase):

    parts_to_load = ['AnyBlok', 'TestAnyBlok']

    def check_order(self, registry, mode, wanted):
        Test = registry.Test
        self.assertEqual(Test.query().filter(Test.mode == mode).all().blok,
                         wanted)

    def test_install(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.check_order(registry, 'install', [
            'test-blok1', 'test-blok2', 'test-blok3'])

    def test_uninstall(self):
        from anyblok.blok import Blok, BlokManager
        old_uninstall = Blok.uninstall

        uninstalled = []

        def uninstall(self):
            cls = self.__class__
            uninstalled.extend(
                [x for x, y in BlokManager.bloks.items() if y is cls])

        try:
            Blok.uninstall = uninstall
            registry = self.init_registry(None)
            self.upgrade(registry, install=('test-blok3',))
            self.upgrade(registry, uninstall=('test-blok1',))
            self.assertEqual(uninstalled, [
                'test-blok3', 'test-blok2', 'test-blok1'])
        finally:
            Blok.uninstall = old_uninstall

    def test_update(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.upgrade(registry, update=('test-blok1',))
        self.check_order(registry, 'update', [
            'test-blok1', 'test-blok2', 'test-blok3'])

    def test_load(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.check_order(registry, 'load', [
            'anyblok-core', 'test-blok1', 'test-blok2', 'test-blok3'])
