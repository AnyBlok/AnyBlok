# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.config import Configuration
from anyblok import (
    load_init_function_from_entry_points,
    configuration_post_load,
)


load_init_function_from_entry_points(unittest=True)
Configuration.load_config_for_test()


class MockParser:

    def _get_kwargs(self):
        return []

    def _get_args(self):
        return False


Configuration.parse_options(MockParser())
configuration_post_load(unittest=True)
