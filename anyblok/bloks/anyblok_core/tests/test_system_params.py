# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Denis VIVIÈS <dvivies@geoblink.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.bloks.anyblok_core.exceptions import ParameterException


@pytest.mark.usefixtures('rollback_registry')
class TestSystemParameter:

    def test_set(self, rollback_registry):
        registry = rollback_registry
        Parameter = registry.System.Parameter
        query = Parameter.query().filter(Parameter.key == 'test.parameter')
        if query.count():
            pytest.fail('key for test already existing')

        Parameter.set('test.parameter', True)
        assert query.count() == 1
        assert query.first().value == {'value': True}
        assert query.first().multi is False

    def test_set_with_multi(self, rollback_registry):
        registry = rollback_registry
        Parameter = registry.System.Parameter
        query = Parameter.query().filter(Parameter.key == 'test.parameter')
        if query.count():
            pytest.fail('key for test already existing')

        Parameter.set('test.parameter', {'test': True})
        assert query.count() == 1
        assert query.first().value == {'test': True}
        assert query.first().multi is True

    def test_get(self, rollback_registry):
        registry = rollback_registry
        Parameter = registry.System.Parameter
        Parameter.set('test.parameter', True)
        assert Parameter.get('test.parameter') is True

    def test_pop(self, rollback_registry):
        registry = rollback_registry
        Parameter = registry.System.Parameter
        assert Parameter.is_exist('test.parameter') is False
        Parameter.set('test.parameter', True)
        assert Parameter.is_exist('test.parameter') is True
        assert Parameter.pop('test.parameter') is True
        assert Parameter.is_exist('test.parameter') is False

    def test_get_with_multi(self, rollback_registry):
        registry = rollback_registry
        Parameter = registry.System.Parameter
        Parameter.set('test.parameter', {'test': True})
        assert Parameter.get('test.parameter') == {'test': True}

    def test_pop_with_multi(self, rollback_registry):
        registry = rollback_registry
        Parameter = registry.System.Parameter
        assert Parameter.is_exist('test.parameter') is False
        Parameter.set('test.parameter', {'test': True})
        assert Parameter.is_exist('test.parameter') is True
        assert Parameter.pop('test.parameter') == {'test': True}
        assert Parameter.is_exist('test.parameter') is False

    def test_unexisting_get(self, rollback_registry):
        registry = rollback_registry
        Parameter = registry.System.Parameter
        with pytest.raises(ParameterException):
            Parameter.get('test.parameter')

    def test_get_with_default(self, rollback_registry):
        registry = rollback_registry
        Parameter = registry.System.Parameter
        assert (
            Parameter.get('test.parameter', default="default value") ==
            "default value"
        )
        assert (
            Parameter.get('test.parameter', "default value") ==
            "default value"
        )
        assert Parameter.get('test.parameter', None) is None
        assert Parameter.get('test.parameter', True) is True
        assert Parameter.get('test.parameter', False) is False

    def test_count(self, rollback_registry):
        registry = rollback_registry
        Parameter = registry.System.Parameter
        assert Parameter.is_exist('test.parameter') is False
        Parameter.set('test.parameter', True)
        assert Parameter.is_exist('test.parameter') is True

    def test_set_existing_key(self, rollback_registry):
        registry = rollback_registry
        Parameter = registry.System.Parameter
        query = Parameter.query().filter(Parameter.key == 'test.parameter')
        assert query.count() == 0
        Parameter.set('test.parameter', True)
        assert query.count() == 1
        assert Parameter.get('test.parameter') is True
        Parameter.set('test.parameter', False)
        assert query.count() == 1
        assert Parameter.get('test.parameter') is False
