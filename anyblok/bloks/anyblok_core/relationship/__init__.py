# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import reload_module_if_blok_is_reloaded
from . import many2one
reload_module_if_blok_is_reloaded(many2one)
from . import one2one
reload_module_if_blok_is_reloaded(one2one)
from . import one2many
reload_module_if_blok_is_reloaded(one2many)
from . import many2many
reload_module_if_blok_is_reloaded(many2many)
