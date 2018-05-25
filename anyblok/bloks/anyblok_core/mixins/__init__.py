# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import reload_module_if_blok_is_reloading

from . import readonly
reload_module_if_blok_is_reloading(readonly)

from . import workflow
reload_module_if_blok_is_reloading(workflow)
