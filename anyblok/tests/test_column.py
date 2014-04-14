from anyblok.tests.testcase import TestCase
from sqlalchemy import Integer as SA_Integer
from anyblok import Declarations
Field = Declarations.Field
Column = Declarations.Column
RelationShip = Declarations.RelationShip
target_registry = Declarations.target_registry
remove_registry = Declarations.remove_registry
FieldException = Declarations.Exception.FieldException


class OneColumn(Column):
    sqlalchemy_type = SA_Integer


class TestColumn(TestCase):

    def test_MustNotBeInstanced(self):
        try:
            Column(label="Test")
            self.fail("Column mustn't be instanced")
        except FieldException:
            pass

    def test_must_have_label(self):
        target_registry(Column, cls_=OneColumn, name_='RealColumn')
        Column.RealColumn(label='test')
        try:
            Column.RealColumn()
            self.fail("No watchdog, the label must be required")
        except FieldException:
            pass

    def test_add_interface(self):
        target_registry(Column, cls_=OneColumn, name_='OneColumn')
        self.assertEqual('Column', Column.OneColumn.__declaration_type__)
        dir(Declarations.Column.OneColumn)

    def test_add_interface_with_decorator(self):

        @target_registry(Column)
        class OneDecoratorColumn(Column):
            sqlalchemy_type = SA_Integer

        self.assertEqual('Column',
                         Column.OneDecoratorColumn.__declaration_type__)
        dir(Declarations.Column.OneDecoratorColumn)

    def test_add_same_interface(self):

        target_registry(Field, cls_=OneColumn, name_="SameColumn")

        try:
            @target_registry(Column)
            class SameColumn(Column):
                sqlalchemy_type = SA_Integer

            self.fail('No watch dog to add 2 same Column')
        except FieldException:
            pass

    def test_remove_interface(self):

        target_registry(Column, cls_=OneColumn, name_="Column2Remove")
        try:
            remove_registry(Column, cls_=OneColumn, name_="Column2Remove")
            self.fail('No watch dog to remove Column')
        except FieldException:
            pass
