# -*- coding: utf-8 -*-
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager


class TestRegistry(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegistry, cls).setUpClass()
        cls.init_argsparse_manager()
        cls.createdb()
        BlokManager.load('AnyBlok')

    def setUp(self):
        super(TestRegistry, self).setUp()
        self.registry = self.getRegistry()

    @classmethod
    def tearDownClass(cls):
        super(TestRegistry, cls).tearDownClass()
        BlokManager.unload()
        cls.dropdb()

    def tearDown(self):
        super(TestRegistry, self).tearDown()
        RegistryManager.clear()

    def test_get(self):
        self.registry.close()
        self.registry = self.getRegistry()

    def test_get_model(self):
        System = self.registry.get('Model.System')
        self.assertEqual(self.registry.System, System)

    def test_get_the_same_registry(self):
        registry = self.getRegistry()
        self.assertEqual(self.registry, registry)

    def test_reload(self):
        bloks_before_reload = self.registry.System.Blok.query('name').filter(
            self.registry.System.Blok.state == 'installed').all()
        self.registry.reload()
        bloks_after_reload = self.registry.System.Blok.query('name').filter(
            self.registry.System.Blok.state == 'installed').all()
        self.assertEqual(bloks_before_reload, bloks_after_reload)
