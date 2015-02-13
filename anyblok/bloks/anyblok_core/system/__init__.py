# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations, reload_module_if_blok_is_reloaded


@Declarations.register(Declarations.Model)
class System:
    pass

from . import model
reload_module_if_blok_is_reloaded(model)
from . import field
reload_module_if_blok_is_reloaded(field)
from . import column
reload_module_if_blok_is_reloaded(column)
from . import relationship
reload_module_if_blok_is_reloaded(relationship)
from . import blok
reload_module_if_blok_is_reloaded(blok)
from . import cache
reload_module_if_blok_is_reloaded(cache)
