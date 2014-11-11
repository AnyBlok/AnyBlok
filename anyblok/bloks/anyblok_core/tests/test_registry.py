from anyblok.tests.testcase import DBTestCase


class TestRegistry(DBTestCase):

    def add_model(self):

        from anyblok import Declarations

        target_registry = Declarations.target_registry
        Model = Declarations.Model
        Integer = Declarations.Column.Integer

        @target_registry(Model)
        class Test:

            id = Integer(primary_key=True)
            val = Integer(default=0)

            @classmethod
            def _precommit_hook(cls):
                for t in cls.query().all():
                    t.val += t.id

            def add_precommit_hook(self):
                self.precommit_hook('_precommit_hook')

            @classmethod
            def add_cl_precommit_hook(cls):
                cls.precommit_hook('_precommit_hook')

    def test_check_dbtestcase_desable_ci(self):
        registry = self.init_registry(self.add_model)
        registry.Test.insert()
        registry.commit()
        self.assertEqual(registry.Test.query().count(), 1)
        registry.rollback()
        self.assertEqual(registry.Test.query().count(), 0)

    def test_precommit_hook(self):
        registry = self.init_registry(self.add_model)
        t1 = registry.Test.insert()
        t1.add_precommit_hook()
        t2 = registry.Test.insert()
        t2.add_precommit_hook()
        self.assertEqual(t1.val, 0)
        self.assertEqual(t2.val, 0)
        registry.commit()
        self.assertEqual(t1.val, t1.id)
        self.assertEqual(t2.val, t2.id)
        registry.commit()
        self.assertEqual(t1.val, t1.id)
        self.assertEqual(t2.val, t2.id)
        registry.Test.add_cl_precommit_hook()
        self.assertEqual(t1.val, t1.id)
        self.assertEqual(t2.val, t2.id)
        registry.commit()
        self.assertEqual(t1.val, 2 * t1.id)
        self.assertEqual(t2.val, 2 * t2.id)
        registry.commit()
        self.assertEqual(t1.val, 2 * t1.id)
        self.assertEqual(t2.val, 2 * t2.id)
        t1.add_precommit_hook()
        self.assertEqual(t1.val, 2 * t1.id)
        self.assertEqual(t2.val, 2 * t2.id)
        registry.commit()
        self.assertEqual(t1.val, 3 * t1.id)
        self.assertEqual(t2.val, 3 * t2.id)
