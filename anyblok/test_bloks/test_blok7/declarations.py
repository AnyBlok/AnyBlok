# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.column import Integer, String
from ..authorization import TestRuleOne, TestRuleTwo


register = Declarations.register
Model = Declarations.Model


@register(Model)
class Test:

    id = Integer(primary_key=True)
    label = String()


@register(Model)
class Test2:

    id = Integer(primary_key=True)
    label = String()


Declarations.AuthorizationBinding(Declarations.Model.Test,
                                  TestRuleOne(),
                                  permission='Read')
Declarations.AuthorizationBinding(Declarations.Model.Test,
                                  TestRuleTwo())
