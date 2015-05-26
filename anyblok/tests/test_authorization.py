# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .testcase import DBTestCase
from ..blok import BlokManager
from anyblok.test_bloks.authorization import TestPolicyOne
from anyblok.test_bloks.authorization import TestPolicyTwo
from anyblok.authorization import deny_all


class TestAuthorizationDeclaration(DBTestCase):

    blok_entry_points = ('bloks', 'test_bloks')

    def tearDown(self):
        super(TestAuthorizationDeclaration, self).tearDown()
        BlokManager.unload()

    def test_association(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok7',))
        record = registry.Test(id=23, label='Hop')
        self.assertIsInstance(registry.lookup_policy(record, 'Read'),
                              TestPolicyOne)
        self.assertIsInstance(registry.lookup_policy(record, 'Other'),
                              TestPolicyTwo)

        record = registry.Test2(id=2, label='Hop')
        self.assertIs(registry.lookup_policy(record, 'Read'), deny_all)

    def test_override(self):
        registry = self.init_registry(None)
        # test-blok8 depends on test-blok7
        self.upgrade(registry, install=('test-blok8',))
        # lookup can be made on model itself
        model = registry.Test
        self.assertIsInstance(registry.lookup_policy(model, 'Read'),
                              TestPolicyOne)
        self.assertIsInstance(registry.lookup_policy(model, 'Other'),
                              TestPolicyOne)
        self.assertIsInstance(registry.lookup_policy(model, 'Write'),
                              TestPolicyTwo)

    def test_model_based_policy(self):
        """Test the model based policy using the default Grant model.

        The policy is defined in the ``model_authz`` blok
        The supporting default model is installed by the same blok.
        #TODO move this test to the 'model_authz' blok
        """
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok9',))
        model = registry.Test2
        Grant = registry.Authorization.ModelPermissionGrant
        Grant.insert(model='Model.Test2',
                     principal="Franck",
                     permission="Read")

        record = model.insert(id=2)
        self.assertTrue(
            registry.check_permission(record, ('Franck',), 'Read'))
        self.assertFalse(
            registry.check_permission(record, ('Franck',), 'Write'))
