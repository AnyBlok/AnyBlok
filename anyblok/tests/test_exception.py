# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok import Declarations
Field = Declarations.Field
Column = Declarations.Column
RelationShip = Declarations.RelationShip
register = Declarations.register
unregister = Declarations.unregister
FieldException = Declarations.Exception.FieldException


class OneInterface:
    pass


class TestCoreInterfaceException(TestCase):

    def test_add_interface(self):
        register(Declarations.Exception, cls_=OneInterface,
                 name_='OneException')
        self.assertEqual(
            'Exception',
            Declarations.Exception.OneException.__declaration_type__)
        dir(Declarations.Exception.OneException)

    def test_add_interface_with_decorator(self):

        @register(Declarations.Exception)
        class OneDecoratorException:
            pass

        self.assertEqual(
            'Exception',
            Declarations.Exception.OneDecoratorException.__declaration_type__)
        dir(Declarations.Exception.OneDecoratorException)

    def test_add_same_interface(self):

        register(Declarations.Exception, cls_=OneInterface,
                 name_="SameException")

        try:
            @register(Declarations.Exception)
            class SameException:
                pass

            self.fail('No watch dog to add 2 same field')
        except Declarations.Exception.DeclarationsException:
            pass

    def test_remove_interface(self):

        register(Declarations.Exception, cls_=OneInterface,
                 name_="Exception2Remove")
        try:
            unregister(Declarations.Exception.Exception2Remove,
                       OneInterface)
            self.fail('No watch dog to remove field')
        except Declarations.Exception.DeclarationsException:
            pass
