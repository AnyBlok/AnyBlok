from anyblok.tests.testcase import TestCase
from anyblok import Declarations
Field = Declarations.Field
Column = Declarations.Column
RelationShip = Declarations.RelationShip
target_registry = Declarations.target_registry
remove_registry = Declarations.remove_registry
FieldException = Declarations.Exception.FieldException


class OneInterface:
    pass


class OneRelationShip(RelationShip):
    pass


class OneModel:
    __tablename__ = 'test'
    __registry_name__ = 'One.Model'


class MockRegistry:

    InstrumentedList = []


class TestRelationShip(TestCase):

    def test_MustNotBeInstanced(self):
        try:
            RelationShip(model=OneModel)
            self.fail("RelationShip mustn't be instanced")
        except FieldException:
            pass

    def test_without_label(self):
        target_registry(RelationShip, cls_=OneRelationShip,
                        name_='NoLabelRelationShip')
        relation = RelationShip.NoLabelRelationShip(model=OneModel)
        relation.get_sqlalchemy_mapping(MockRegistry(), None,
                                        'a_relation_ship', None)
        self.assertEqual(relation.label, 'A relation ship')

    def test_must_have_a_model(self):
        target_registry(RelationShip, cls_=OneRelationShip,
                        name_="RealRelationShip")
        RelationShip.RealRelationShip(model=OneModel)
        try:
            RelationShip.RealRelationShip()
            self.fail("No watchdog, the model must be required")
        except FieldException:
            pass

    def test_add_interface(self):
        target_registry(RelationShip, cls_=OneRelationShip)
        self.assertEqual('RelationShip',
                         RelationShip.OneRelationShip.__declaration_type__)
        dir(Declarations.RelationShip.OneRelationShip)

    def test_add_interface_with_decorator(self):

        @target_registry(RelationShip)
        class OneDecoratorRelationShip(RelationShip):
            pass

        self.assertEqual(
            'RelationShip',
            RelationShip.OneDecoratorRelationShip.__declaration_type__)
        dir(Declarations.RelationShip.OneDecoratorRelationShip)

    def test_add_same_interface(self):

        target_registry(RelationShip, cls_=OneRelationShip,
                        name_="SameRelationShip")

        try:
            @target_registry(RelationShip)
            class SameRelationShip(RelationShip):
                pass

            self.fail('No watch dog to add 2 same relation ship')
        except FieldException:
            pass

    def test_remove_interface(self):

        target_registry(RelationShip, cls_=OneRelationShip,
                        name_="RelationShip2Remove")
        try:
            remove_registry(RelationShip, cls_=OneRelationShip,
                            name_="RelationShip2Remove")
            self.fail('No watch dog to remove relation ship')
        except FieldException:
            pass
