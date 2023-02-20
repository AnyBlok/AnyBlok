# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.column import Integer, String
from anyblok.declarations import Declarations

register = Declarations.register
Model = Declarations.Model


@register(Model)
class Test:
    id = Integer(primary_key=True)
    mode = String()
