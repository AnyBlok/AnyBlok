# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Authorization subframework.

The founding principle of authorization handling within Anyblok is to check
authorization explicitely at the edge of the system (for instance,
for applications
exposed over HTTP, that would be in the controllers), because that is where the
idea of user, or slightly more generally, has functional semantics that can
be interpreted in the context of a given action.

In that spirit, we don't pass the user to the core framework and business
layers.
Instead, these provide *policies* to check permissions on records or query
records according to the.

The declarations at the edge will *associate* the policies with the
models. The edge user-aware methods will call the check and query facilities
provided by the core that themselves apply the relevant policies.
"""
