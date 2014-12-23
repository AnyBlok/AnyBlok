# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
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
        if not BlokManager.has('anyblok-core'):
            self.fail("The blok 'anyblok-core' is missing")

        BlokManager.get('anyblok-core')

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
