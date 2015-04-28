# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations, reload_module_if_blok_is_reloaded


@Declarations.register(Declarations.Model)
class System:
    pass

from . import model  # noqa
reload_module_if_blok_is_reloaded(model)
from . import field  # noqa
reload_module_if_blok_is_reloaded(field)
from . import column  # noqa
reload_module_if_blok_is_reloaded(column)
from . import relationship  # noqa
reload_module_if_blok_is_reloaded(relationship)
from . import blok  # noqa
reload_module_if_blok_is_reloaded(blok)
from . import cache  # noqa
reload_module_if_blok_is_reloaded(cache)
from . import parameter  # noqa
reload_module_if_blok_is_reloaded(parameter)
from . import sequence  # noqa
reload_module_if_blok_is_reloaded(sequence)
