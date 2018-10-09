# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.blok import BlokManager, Blok, BlokManagerException


class TestBlokManager:

    @pytest.fixture(autouse=True)
    def bloks_must_be_unloaded(self, request):
        request.addfinalizer(BlokManager.unload)
        BlokManager.unload()

    def test_load_anyblok(self):
        BlokManager.load()
        if not BlokManager.list():
            pytest.fail('No blok load')
        if not BlokManager.has('anyblok-core'):
            pytest.fail("The blok 'anyblok-core' is missing")

        BlokManager.get('anyblok-core')

    def test_load_with_invalid_blok_group(self):
        with pytest.raises(BlokManagerException):
            BlokManager.load(entry_points=('Invalid blok group',))

    def test_load_without_blok_group(self):
        with pytest.raises(BlokManagerException):
            BlokManager.load(entry_points=())

    def test_reload(self):
        BlokManager.load()
        BlokManager.set('invalid blok', None)
        BlokManager.get('invalid blok')
        BlokManager.reload()
        with pytest.raises(BlokManagerException):
            BlokManager.get('invalid blok')

    def test_reload_without_load(self):
        with pytest.raises(BlokManagerException):
            BlokManager.reload()

    def test_get_invalid_blok(self):
        BlokManager.load()
        with pytest.raises(BlokManagerException):
            BlokManager.get('invalid blok')

    def test_set(self):
        blok_name = 'ABlok'
        BlokManager.set(blok_name, Blok)
        assert BlokManager.has(blok_name)

    def test_set_two_time(self):
        blok_name = 'ABlok'
        BlokManager.set(blok_name, Blok)
        with pytest.raises(BlokManagerException):
            BlokManager.set(blok_name, Blok)
