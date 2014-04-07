# -*- coding: utf-8 -*-
from .anybloktestcase import AnyBlokTestCase
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager
import AnyBlok


class AnyBlokFieldTestCase(AnyBlokTestCase):

    @classmethod
    def setUpClass(cls):
        super(AnyBlokFieldTestCase, cls).setUpClass()
        cls.init_argsparse_manager()

    def setUp(self):
        super(AnyBlokFieldTestCase, self).setUp()
        self.createdb()
        BlokManager.load('AnyBlok')

    def tearDown(self):
        RegistryManager.clear()
        BlokManager.unload()
        self.dropdb()
        super(AnyBlokFieldTestCase, self).tearDown()

    def init_registry(self, function, **kwargs):
        AnyBlok.current_blok = 'anyblok-core'
        function(**kwargs)
        AnyBlok.current_blok = None
        return self.getRegistry()
