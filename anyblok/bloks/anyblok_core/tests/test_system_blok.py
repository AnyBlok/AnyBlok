from anyblok.tests.testcase import BlokTestCase


class TestSystemBlok(BlokTestCase):

    def test_list_by_state_installed(self):
        installed = self.registry.System.Blok.list_by_state('installed')
        core_is_installed = 'anyblok-core' in installed
        self.assertEqual(core_is_installed, True)

    def test_list_by_state_without_state(self):
        self.assertEqual(self.registry.System.Blok.list_by_state(), None)
