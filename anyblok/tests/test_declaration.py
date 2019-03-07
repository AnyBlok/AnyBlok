# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok import Declarations
from anyblok.declarations import DeclarationsException


class OneType:

    @classmethod
    def register(cls, parent, name, cls_, **kwargs):
        setattr(parent, name, cls_)

    @classmethod
    def unregister(cls, entry, cls_):
        pass


class TestDeclaration:

    @pytest.fixture(autouse=True)
    def tearDown(self, request):

        def reset():
            for type_ in ['OneType', 'MyOneType']:
                if type_ in Declarations.declaration_types:
                    del Declarations.declaration_types[type_]

        request.addfinalizer(reset)

    def test_add(self):
        Declarations.add_declaration_type(cls_=OneType)
        assert Declarations.declaration_types['OneType'] == OneType

        class SubType:
            pass

        Declarations.register(Declarations.OneType, cls_=SubType)
        Declarations.unregister(Declarations.OneType, cls_=SubType)

    def test_add_doublon(self):
        Declarations.add_declaration_type(cls_=OneType)
        try:
            Declarations.add_declaration_type(cls_=OneType)
            self.fail('No watch dog for doublon declarations type')
        except DeclarationsException:
            pass

    def test_add_decoration(self):

        @Declarations.add_declaration_type()
        class MyOneType(OneType):
            pass

        assert Declarations.declaration_types['MyOneType'] == MyOneType

        @Declarations.register(Declarations.MyOneType)
        class SubType:
            pass

        Declarations.unregister(Declarations.MyOneType.SubType, SubType)
