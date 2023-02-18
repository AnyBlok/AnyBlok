# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.column import String, Json, Boolean
from ..exceptions import ParameterException


register = Declarations.register
System = Declarations.Model.System

NOT_PROVIDED = object


@register(Declarations.Model.System)
class Parameter:
    """Applications parameters.

    This Model is provided by ``anyblok-core`` to give applications a uniform
    way of specifying in-database configuration.

    It is a simple key/value representation, where values can be of any type
    that can be encoded as JSON.

    A simple access API is provided with the :meth:`get`, :meth:`set`,
    :meth:`is_exist` and further methods.
    """

    key = String(primary_key=True)
    value = Json(nullable=False)
    multi = Boolean(default=False)

    @classmethod
    def set(cls, key, value):
        """ Insert or update parameter value for a key.

        .. note:: if the key already exists, the value will be updated

        :param str key: key to save
        :param value: value to save
        """
        multi = False
        if not isinstance(value, dict):
            value = {'value': value}
        else:
            multi = True

        if cls.is_exist(key):
            param = cls.from_primary_keys(key=key)
            param.update(value=value, multi=multi)
        else:
            cls.insert(key=key, value=value, multi=multi)

    @classmethod
    def is_exist(cls, key):
        """ Check if one parameter exist for the key

        :param key: key to check
        :rtype: bool
        """
        query = cls.query().filter(cls.key == key)
        return True if query.count() else False

    @classmethod
    def get_parameter(cls, key, default=NOT_PROVIDED, remove=False):
        """ Return the value of the key

        :param key: key whose value to retrieve
        :param default: default value if key does not exists
        :param remove: bool if True the entry will be removed
        :return: associated value
        :rtype: anything JSON encodable
        :raises ParameterException: if the key doesn't exist and default is not
                                    set.
        """
        if not cls.is_exist(key):
            if default is NOT_PROVIDED:
                raise ParameterException(
                    "unexisting key %r" % key)
            return default

        param = cls.from_primary_keys(key=key)
        if param.multi:
            res = param.value
        else:
            res = param.value['value']

        if remove:
            param.delete()

        return res

    @classmethod
    def get(cls, key, default=NOT_PROVIDED):
        """ Return the value of the key

        :param key: key whose value to retrieve
        :param default: default value if key does not exists
        :return: associated value
        :rtype: anything JSON encodable
        :raises ParameterException: if the key doesn't exist and default is not
                                    set.
        """
        return cls.get_parameter(key, default=default)

    @classmethod
    def pop(cls, key, default=NOT_PROVIDED):
        """Remove the given key and return the associated value.

        :param str key: the key to remove
        :return: the value before removal
        :param default: default value if key does not exists
        :rtype: any JSON encodable type
        :raises ParameterException: if the key wasn't present
        """
        return cls.get_parameter(key, default=default, remove=True)
