# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.

from anyblok import Declarations
from anyblok.authorization.rule.base import deny_all


@Declarations.register(Declarations.Model)
class Authorization:
    """Namespace for models supporting authorization policies."""


class DefaultModelDeclaration:
    """Pseudo model to represent the default value."""

    __registry_name__ = None


Declarations.AuthorizationBinding(DefaultModelDeclaration, deny_all)
