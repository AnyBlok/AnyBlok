# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase


class TestCoreQuery(DBTestCase):

    def test_inherit(self):

        def inherit():

            from anyblok import Declarations
            Core = Declarations.Core

            @Declarations.register(Core)
            class Query:

                def foo(self):
                    return True

        registry = self.init_registry(inherit)
        self.assertEqual(registry.System.Blok.query().foo(), True)
