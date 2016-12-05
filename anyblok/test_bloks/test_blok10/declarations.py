# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.column import String
from anyblok.authorization.rule.modelaccess import ModelAccessRule
from anyblok.authorization.rule.attraccess import AttributeAccessRule


register = Declarations.register
Model = Declarations.Model


@register(Model)
class Test2:
    """We'll work on Test2, on which test_blok7 doesn't set any authz policy.
    """
    owner = String()


Declarations.AuthorizationBinding(
    Declarations.Model.Test2,
    ModelAccessRule())

Declarations.AuthorizationBinding(
    Declarations.Model.Test2,
    AttributeAccessRule('owner'),
    permission='Write')

Declarations.AuthorizationBinding(
    Declarations.Model.Test2,
    AttributeAccessRule('owner', model_rule=ModelAccessRule()),
    permission='PermWithModelRule')
