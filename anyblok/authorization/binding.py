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
from copy import deepcopy

from ..declarations import Declarations
from ..environment import EnvironmentManager
from ..registry import RegistryManager


@Declarations.add_declaration_type(isAnEntry=True,
                                   assemble='assemble_callback')
class AuthorizationBinding:
    """Encodes which policy to use per model or (model, permission).

    In the assembly phase, copies of the policy are issued, and the registry
    is set as an attribute on them. This is a bit memory inefficient, but
    otherwise, passing the registry would have to be in all AuthorizationRule
    API calls.
    """

    def __new__(cls, model_declaration, policy, permission=None):
        """Declare for given model that policy should be used.

        :param permission: if provided, the policy will apply for this
                           permission only, otherwise, it will act as the
                           default policy for this model.
        """
        cb = EnvironmentManager.get('current_blok')
        model = model_declaration.__registry_name__
        key = (model, permission) if permission is not None else model
        blok_declarations = RegistryManager.loaded_bloks[cb][cls.__name__]
        blok_declarations[key] = policy

    @classmethod
    def assemble_callback(cls, registry):
        policies = {}
        for blok in registry.ordered_loaded_bloks:
            policies.update(RegistryManager.loaded_bloks[blok][cls.__name__])

        # for this registry entry, the list of names is irrelevant pollution:
        del policies['registry_names']
        registry._authz_policies = deepcopy(policies)
        for policy in registry._authz_policies.values():
            policy.registry = registry
