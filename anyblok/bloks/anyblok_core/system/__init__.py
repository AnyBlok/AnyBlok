# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations, reload_module_if_blok_is_reloading


@Declarations.register(Declarations.Model)
class System:
    pass

from . import model
reload_module_if_blok_is_reloading(model)
from . import field
reload_module_if_blok_is_reloading(field)
from . import column
reload_module_if_blok_is_reloading(column)
from . import relationship
reload_module_if_blok_is_reloading(relationship)
from . import blok
reload_module_if_blok_is_reloading(blok)
from . import cache
reload_module_if_blok_is_reloading(cache)
from . import parameter
reload_module_if_blok_is_reloading(parameter)
from . import sequence
reload_module_if_blok_is_reloading(sequence)
from . import cron
reload_module_if_blok_is_reloading(cron)
