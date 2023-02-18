# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest  # noqa
from anyblok.blok import BlokManager
from .conftest import init_registry


@pytest.fixture(scope="module")
def bloks_loaded(request, configuration_loaded):
    request.addfinalizer(BlokManager.unload)
    BlokManager.load()


class TestCoreQuery:

    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):

        def close():
            if hasattr(self, 'registry'):
                self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def test_inherit(self):

        def inherit():

            from anyblok import Declarations
            Core = Declarations.Core

            @Declarations.register(Core)
            class Query:

                def foo(self):
                    return True

        registry = self.init_registry(inherit)
        assert registry.System.Blok.query().foo() is True
