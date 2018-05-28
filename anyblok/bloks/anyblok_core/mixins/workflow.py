# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from ..exceptions import WorkFlowException
Mixin = Declarations.Mixin


@Declarations.register(Mixin)
class WorkFlow(Mixin.StateReadOnly):

    WORKFLOW = {}

    @classmethod  # should be a cache classmethod
    def get_workflow_definition(cls):
        return cls.WORKFLOW

    @classmethod
    def get_default_state(cls):
        workflow = cls.get_workflow_definition()
        defaults = [key
                    for key, value in workflow.items()
                    if value.get('default')]

        if len(defaults) != 1:
            raise WorkFlowException(
                ("Only one default value is wanted on model %r. "
                 "%d given %r" % (cls, len(defaults), defaults)))

        return defaults[0]

    @classmethod
    def get_states(cls):
        workflow = cls.get_workflow_definition()
        if not workflow:
            raise WorkFlowException(
                "No workflow defined on the model %r" % cls)

        return {key: value.get('label', key.capitalize)
                for key, value in workflow.items()}

    def state_to(self, new_state):
        self.state = new_state
        self.registry.flush()

    def validate_conditions(self, conditions):
        if not isinstance(conditions, (list, tuple)):
            conditions = [conditions]

        for condition in conditions:
            if isinstance(condition, bool) and not condition:
                return False, condition
            elif isinstance(condition, str):
                if not getattr(self, condition)():
                    return False, condition
            elif not isinstance(condition, bool) and not condition(self):
                return False, condition

        return True, None

    def check_if_forbid_update_condition_is_true(self, **previous_values):
        workflow = self.__class__.get_workflow_definition().get(self.state)
        if 'state' in previous_values:
            previous_workflow = self.__class__.get_workflow_definition().get(
                previous_values['state'])
            allowed_to = previous_workflow.get('allowed_to', [])
            if isinstance(allowed_to, (list, tuple)):
                allowed_to = {
                    key[0] if isinstance(key, (list, tuple)) else key:
                    key[1] if isinstance(key, (list, tuple)) else True
                    for key in allowed_to}

            if self.state not in allowed_to:
                raise WorkFlowException(
                    "No rules found to change state from %r to %r" % (
                        previous_values['state'], self.state))

            conditions = allowed_to[self.state]
            validated, condition = self.validate_conditions(conditions)
            if not validated:
                raise WorkFlowException(
                    ("[%r] You can not change the state from %r to "
                     "%r" % (condition, previous_values['state'],
                             self.state)))

        elif workflow.get('readonly'):
            return True

        validated, condition = self.validate_conditions(
            workflow.get('validators', []))
        if not validated:
            raise WorkFlowException(
                ("[%r] Not validate the current changed %r => %r for state "
                 "%r" % (condition, previous_values,
                         {key: getattr(self, key)
                          for key in previous_values.keys()},
                         self.state)))

    @classmethod
    def before_update_orm_event(cls, mapper, connection, target):
        modified_fields = target.get_modified_fields()
        if 'state' in modified_fields:
            workflow = target.__class__.get_workflow_definition().get(
                target.state)
            apply_change = workflow.get('apply_change', [])
            if isinstance(apply_change, dict):
                apply_change = apply_change.get(modified_fields['state'], [])

            if not isinstance(apply_change, (tuple, list)):
                apply_change = [apply_change]

            for ap in apply_change:
                getattr(target, ap)(modified_fields['state'])

        super(WorkFlow, cls).before_update_orm_event(
            mapper, connection, target)

    def check_if_forbid_delete_condition_is_true(self):
        workflow = self.__class__.get_workflow_definition().get(self.state)
        if workflow.get('readonly'):
            return not workflow.get('deletable', False)

        if 'deletable' in workflow:
            return not workflow['deletable']
