# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from sqlalchemy import Integer as SA_Integer
from anyblok import Declarations
Field = Declarations.Field
Column = Declarations.Column
RelationShip = Declarations.RelationShip
register = Declarations.register
unregister = Declarations.unregister
FieldException = Declarations.Exception.FieldException


class OneColumn(Column):
    sqlalchemy_type = SA_Integer


class TestColumn(TestCase):

    def test_forbid_instance(self):
        try:
            Column()
            self.fail("Column mustn't be instanciated")
        except FieldException:
            pass

    def test_without_label(self):
        register(Column, cls_=OneColumn, name_='RealColumn')
        column = Column.RealColumn()
        column.get_sqlalchemy_mapping(None, None, 'a_column', None)
        self.assertEqual(column.label, 'A column')

    def test_add_interface(self):
        register(Column, cls_=OneColumn, name_='OneColumn')
        self.assertEqual('Column', Column.OneColumn.__declaration_type__)
        dir(Declarations.Column.OneColumn)

    def test_add_interface_with_decorator(self):

        @register(Column)
        class OneDecoratorColumn(Column):
            sqlalchemy_type = SA_Integer

        self.assertEqual('Column',
                         Column.OneDecoratorColumn.__declaration_type__)
        dir(Declarations.Column.OneDecoratorColumn)

    def test_add_same_interface(self):

        register(Field, cls_=OneColumn, name_="SameColumn")

        try:
            @register(Column)
            class SameColumn(Column):
                sqlalchemy_type = SA_Integer

            self.fail('No watch dog to add 2 same Column')
        except FieldException:
            pass

    def test_remove_interface(self):

        register(Column, cls_=OneColumn, name_="Column2Remove")
        try:
            unregister(Column.Column2Remove, OneColumn)
            self.fail('No watch dog to remove Column')
        except FieldException:
            pass
