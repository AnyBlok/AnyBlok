.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2020 Pierre Verkest <pierreverkest84@gmail.com>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

Test blok16
===========

Test Blok16 is used to validate the order of calls over following methods:

* pre_migration
* post_migration
* update
* update_demo

* uninstall
* uninstall_demo

In différent cases playing with following options:

* with-demo system parameter
* withoutautomigration
* loadwithoutmigration

