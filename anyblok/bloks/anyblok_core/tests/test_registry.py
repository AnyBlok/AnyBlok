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

    def define_cls(self, typename='Model', name='Test', val=1, usesuper=False,
                   inherit=None):

        from anyblok import Declarations

        target_registry = Declarations.target_registry
        Type = getattr(Declarations, typename)
        if inherit is None:
            inherit = object
        else:
            inherit = getattr(Declarations.Mixin, inherit)

        @target_registry(Type, name_=name)
        class Test(inherit):

            @classmethod
            def foo(cls):
                if usesuper:
                    return val * super(Test, cls).foo()

                return val

        return Test

    def test_check_define_cls(self):

        def add_in_registry():
            self.define_cls()

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 1)

    def test_check_define_cls_with_inherit(self):

        def add_in_registry():
            self.define_cls()
            self.define_cls(val=2, usesuper=True)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 2)

    def test_check_define_cls_with_inherit_core(self):

        def add_in_registry():
            self.define_cls(typename='Core', name='Base', val=2)
            self.define_cls(val=2, usesuper=True)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 4)

    def test_check_define_cls_with_inherit_mixin(self):

        def add_in_registry():
            self.define_cls(typename='Mixin', name='MTest', val=3)
            self.define_cls(val=3, usesuper=True, inherit='MTest')

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 9)

    def test_check_define_cls_with_inherit2(self):

        def add_in_registry():
            self.define_cls()
            self.define_cls(val=2, usesuper=True)
            self.define_cls(val=2, usesuper=True)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 4)

    def test_check_define_cls_with_inherit_core2(self):

        def add_in_registry():
            self.define_cls(typename='Core', name='Base', val=2)
            self.define_cls(typename='Core', name='Base', val=2, usesuper=True)
            self.define_cls(val=2, usesuper=True)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 8)

    def test_check_define_cls_with_inherit_mixin2(self):

        def add_in_registry():
            self.define_cls(typename='Mixin', name='MTest', val=3)
            self.define_cls(typename='Mixin', name='MTest', val=3,
                            usesuper=True)
            self.define_cls(val=3, usesuper=True, inherit='MTest')

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 27)

    def test_remove(self):

        def add_in_registry():
            self.define_cls()
            cls_ = self.define_cls(val=2, usesuper=True)
            self.define_cls(val=2, usesuper=True)
            from anyblok import Declarations
            Declarations.remove_registry(Declarations.Model.Test, cls_)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 2)

    def test_remove_core(self):

        def add_in_registry():
            self.define_cls(typename='Core', name='Base', val=2)
            cls_ = self.define_cls(typename='Core', name='Base', val=2,
                                   usesuper=True)
            self.define_cls(val=2, usesuper=True)
            from anyblok import Declarations
            Declarations.remove_registry(Declarations.Core.Base, cls_)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 4)

    def test_remove_mixin(self):

        def add_in_registry():
            self.define_cls(typename='Mixin', name='MTest', val=3)
            cls_ = self.define_cls(typename='Mixin', name='MTest', val=3,
                                   usesuper=True)
            self.define_cls(val=3, usesuper=True, inherit='MTest')
            from anyblok import Declarations
            Declarations.remove_registry(Declarations.Mixin.MTest, cls_)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 9)
