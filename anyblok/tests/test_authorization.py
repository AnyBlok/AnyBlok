# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .testcase import DBTestCase
from ..blok import BlokManager
from ..authorization.policy import deny_all
from ..authorization.policy import PolicyNotForModelClasses
from anyblok.bloks.attr_authz import AttributeBasedAuthorizationPolicy
from anyblok.test_bloks.authorization import TestPolicyOne
from anyblok.test_bloks.authorization import TestPolicyTwo


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

        # With this policy, permission can be checked on the model
        self.assertTrue(
            registry.check_permission(model, ('Franck',), 'Read'))
        self.assertFalse(
            registry.check_permission(model, ('Franck',), 'Write'))

        query = model.query().filter(model.id != 1)
        self.assertEqual(query.count(), 1)

        filtered = registry.query_permission(query, ('Franck',), 'Read',
                                             models=(model,))
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().id, 2)
        all_results = filtered.all()
        self.assertEqual(all_results[0].id, 2)

        filtered = registry.query_permission(query, ('Franck',), 'Write',
                                             models=(model,))
        self.assertEqual(filtered.count(), 0)
        self.assertIsNone(filtered.first())
        self.assertEqual(len(filtered.all()), 0)

    def test_attr_based_policy(self):
        """Test the attribute based policy, in conjunction with the model one.

        The policy is defined in the ``attr_authz`` blok
        The supporting default model is installed by the same blok.
        TODO move this test to the 'attr_authz' blok, or put the policy in the
        main code body.
        """
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok10',))
        model = registry.Test2
        Grant = registry.Authorization.ModelPermissionGrant
        Grant.insert(model='Model.Test2',
                     principal="Franck",
                     permission="Read")
        Grant.insert(model='Model.Test2',
                     principal="Georges",
                     permission="Read")

        # We also test that this entry is ignored, because it is
        # superseded by attribute-based policy
        Grant.insert(model='Model.Test',
                     principal="Franck",
                     permission="Write")

        record = model.insert(id=1, owner='Georges')
        self.assertTrue(
            registry.check_permission(record, ('Franck',), 'Read'))
        self.assertTrue(
            registry.check_permission(record, ('Georges',), 'Write'))
        self.assertFalse(
            registry.check_permission(record, ('Franck',), 'Write'))

        # With this policy, permission cannot be checked on the model
        with self.assertRaises(PolicyNotForModelClasses) as arc:
            registry.check_permission(model, ('Franck',), 'Write')
        self.assertIsInstance(arc.exception.policy,
                              AttributeBasedAuthorizationPolicy)

        model.insert(id=2, owner='Franck')
        model.insert(id=3, owner='JS')

        query = model.query()
        self.assertEqual(query.count(), 3)

        filtered = registry.query_permission(query, ('Franck',), 'Write',
                                             models=(model,))

        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().id, 2)
        all_results = filtered.all()
        self.assertEqual(all_results[0].id, 2)

        filtered = registry.query_permission(query, ('Franck',), 'Read',
                                             models=(model,))
        self.assertEqual(filtered.count(), 3)

        filtered = registry.query_permission(query, ('Franck', 'Georges',),
                                             'Write',
                                             models=(model,))
        self.assertEqual(filtered.count(), 2)
        self.assertEqual([r.id for r in filtered.all()], [1, 2])
