# This file is a part of the AnyBlok project
#
#    Copyright (C) 2024 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest


@pytest.mark.usefixtures("rollback_registry")
class TestCoreSession:
    def test_anyblok_in_session(self, rollback_registry):
        assert rollback_registry.session.anyblok is rollback_registry

    def test_anyblok_in_session_query(self, rollback_registry):
        assert rollback_registry.session._query_cls.anyblok is rollback_registry
