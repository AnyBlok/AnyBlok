# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .testcase import DBTestCase
from ..authorization.rule.base import deny_all
from ..authorization.rule.base import RuleNotForModelClasses
from ..authorization.rule.attraccess import AttributeAccessRule
from anyblok.test_bloks.authorization import TestRuleOne
from anyblok.test_bloks.authorization import TestRuleTwo


class TestAuthorizationDeclaration(DBTestCase):

    blok_entry_points = ('bloks', 'test_bloks')

    def test_association(self):
        registry = self.init_registry(None)
        registry.upgrade(install=('test-blok7',))
        record = registry.Test(id=23, label='Hop')
        self.assertIsInstance(registry.lookup_policy(record, 'Read'),
                              TestRuleOne)
        self.assertIsInstance(registry.lookup_policy(record, 'Other'),
                              TestRuleTwo)

        record = registry.Test2(id=2, label='Hop')
        self.assertIs(registry.lookup_policy(record, 'Read'), deny_all)

    def test_override(self):
        # test-blok8 depends on test-blok7
        registry = self.init_registry(None)
        registry.upgrade(install=('test-blok8',))
        # lookup can be made on model itself
        model = registry.Test
        self.assertIsInstance(registry.lookup_policy(model, 'Read'),
                              TestRuleOne)
        self.assertIsInstance(registry.lookup_policy(model, 'Other'),
                              TestRuleOne)
        self.assertIsInstance(registry.lookup_policy(model, 'Write'),
                              TestRuleTwo)

    def test_model_based_policy(self):
        """Test the model based policy using the default Grant model.

        The policy is defined in the ``model_authz`` blok
        The supporting default model is installed by the same blok.
        #TODO move this test to the 'model_authz' blok
        """
        registry = self.init_registry(None)
        registry.upgrade(install=('test-blok9',))
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

        # This can be also called directly from the model class
        self.assertTrue(model.has_model_perm(('Franck',), 'Read'))
        self.assertFalse(model.has_model_perm(('Franck',), 'Write'))
        with self.assertRaises(TypeError):
            model.has_perm(('Franck',), 'Write')

        query = model.query().filter(model.id != 1)
        self.assertEqual(query.count(), 1)

        filtered = registry.wrap_query_permission(
            query, ('Franck',), 'Read')
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().id, 2)
        all_results = filtered.all()
        self.assertEqual(all_results[0].id, 2)

        filtered = registry.wrap_query_permission(
            query, ('Franck',), 'Write')
        self.assertEqual(filtered.count(), 0)
        self.assertIsNone(filtered.first())
        self.assertEqual(len(filtered.all()), 0)

        # the same can be achieved from the query
        filtered = query.with_perm(('Franck',), 'Read')
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().id, 2)
        all_results = filtered.all()
        self.assertEqual(all_results[0].id, 2)

        filtered = query.with_perm(('Franck',), 'Write')
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
        registry.upgrade(install=('test-blok10',))
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

        # The same checks can be done from the record
        self.assertTrue(record.has_perm(('Franck',), 'Read'))
        self.assertTrue(record.has_perm(('Georges',), 'Write'))
        self.assertFalse(record.has_perm(('Franck',), 'Write'))

        # With this policy, permission cannot be checked on the model
        with self.assertRaises(RuleNotForModelClasses) as arc:
            registry.check_permission(model, ('Franck',), 'Write')
        self.assertIsInstance(arc.exception.policy,
                              AttributeAccessRule)

        # ... unless one defines a model_rule to handle the case
        self.assertFalse(registry.check_permission(
            model, ('Franck',), 'PermWithModelRule'))

        Grant = registry.Authorization.ModelPermissionGrant
        Grant.insert(model=model.__registry_name__,
                     principal="Franck",
                     permission="PermWithModelRule")
        self.assertTrue(registry.check_permission(
            model, ('Franck',), 'PermWithModelRule'))
        self.assertFalse(record.has_perm(('Franck',), 'PermWithModelRule'))

        # Query wrapping tests

        model.insert(id=2, owner='Franck')
        model.insert(id=3, owner='JS')

        query = model.query()
        self.assertEqual(query.count(), 3)

        filtered = registry.wrap_query_permission(
            query, ('Franck',), 'Write')

        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().id, 2)
        all_results = filtered.all()
        self.assertEqual(all_results[0].id, 2)

        # The same can be achieved directly on query
        filtered = query.with_perm(('Franck',), 'Write')
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().id, 2)
        all_results = filtered.all()
        self.assertEqual(all_results[0].id, 2)

        filtered = registry.wrap_query_permission(
            query, ('Franck',), 'Read')
        self.assertEqual(filtered.count(), 3)

        filtered = registry.wrap_query_permission(
            query, ('Franck', 'Georges',), 'Write')
        self.assertEqual(filtered.count(), 2)
        self.assertEqual([r.id for r in filtered.all()], [1, 2])
