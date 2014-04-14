# -*- coding: utf-8 -*-
from anyblok.blok import BlokManager, Blok
from anyblok.tests.testcase import TestCase
from anyblok import Declarations


BlokManagerException = Declarations.Exception.BlokManagerException


class TestBlokManager(TestCase):

    def tearDown(self):
        super(TestBlokManager, self).tearDown()
        BlokManager.unload()

    def test_load_anyblok(self):
        BlokManager.load('AnyBlok')
        if not BlokManager.list():
            self.fail('No blok load')
        if not BlokManager.has('anyblok_core'):
            self.fail("The blok 'anyblok_core' is missing")

        BlokManager.get('anyblok_core')

    def test_load_with_invalid_blok_group(self):
        try:
            BlokManager.load('Invalid blok group')
            self.fail('Load with invalid blok group')
        except BlokManagerException:
            pass

    def test_load_without_blok_group(self):
        try:
            BlokManager.load()
            self.fail('No watchdog to load without blok groups')
        except BlokManagerException:
            pass

    def test_reload(self):
        BlokManager.load('AnyBlok')
        BlokManager.set('invalid blok', None)
        BlokManager.get('invalid blok')
        BlokManager.reload()
        try:
            BlokManager.get('invalid blok')
            self.fail("Reload classmethod doesn't reload the bloks")
        except BlokManagerException:
            pass

    def test_reload_without_load(self):
        try:
            BlokManager.reload()
            self.fail('No exception when reload without previously load')
        except BlokManagerException:
            pass

    def test_get_invalid_blok(self):
        try:
            BlokManager.load('AnyBlok')
            BlokManager.get('invalid blok')
            self.fail('No exception when get invalid blok')
        except BlokManagerException:
            pass

    def test_get_files_from(self):
        BlokManager.load('AnyBlok')
        BlokManager.get_files_from('anyblok_core', 'css')

    def test_set(self):
        blok_name = 'ABlok'
        BlokManager.set(blok_name, Blok)
        self.assertEqual(BlokManager.has(blok_name), True)

    def test_set_two_time(self):
        blok_name = 'ABlok'
        BlokManager.set(blok_name, Blok)
        try:
            BlokManager.set(blok_name, Blok)
            self.fail("No watch dog for set two time the same blok")
        except BlokManagerException:
            pass
