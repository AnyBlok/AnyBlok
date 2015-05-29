# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.column import Integer
from ..authorization import TestRuleOne, TestRuleTwo

register = Declarations.register
Model = Declarations.Model


@register(Model)
class Test:

    test2 = Integer(foreign_key=(Model.Test2, 'id'))

Declarations.AuthorizationRuleAssociation(Declarations.Model.Test,
                                          TestRuleOne(),
                                          permission='Other')
Declarations.AuthorizationRuleAssociation(Declarations.Model.Test,
                                          TestRuleOne())
Declarations.AuthorizationRuleAssociation(Declarations.Model.Test,
                                          TestRuleTwo(),
                                          permission='Write')
