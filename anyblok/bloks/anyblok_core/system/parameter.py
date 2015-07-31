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


@register(Declarations.Model.System)
class Parameter:
    """System Parameter"""

    key = String(primary_key=True)
    value = Json(nullable=False)
    multi = Boolean(default=False)

    @classmethod
    def set(cls, key, value):
        """ Insert or Update parameter for the key

        :param key: key to save
        :param value: value to save
        """
        multi = False
        if not isinstance(value, dict):
            value = {'value': value}
        else:
            multi = True

        if cls.is_exist(key):
            param = cls.from_primary_keys(key=key)
            param.update(dict(value=value, multi=multi))
        else:
            cls.insert(key=key, value=value, multi=multi)

    @classmethod
    def is_exist(cls, key):
        """ Check if one parameter exist for the key

        :param key: key to check
        :rtype: Boolean, True if exist
        """
        query = cls.query().filter(cls.key == key)
        return True if query.count() else False

    @classmethod
    def get(cls, key):
        """ Return the value of the key

        :param key: key to check
        :rtype: return value
        :exception: ExceptionParameter
        """
        if not cls.is_exist(key):
            raise ParameterException(
                "unexisting key %r" % key)

        param = cls.from_primary_keys(key=key)
        if param.multi:
            return param.value

        return param.value['value']

    @classmethod
    def pop(cls, key):
        """Remove return the value of the key

        :param key: key to check
        :rtype: return value
        :exception: ExceptionParameter
        """
        if not cls.is_exist(key):
            raise ParameterException(
                "unexisting key %r" % key)

        param = cls.from_primary_keys(key=key)
        if param.multi:
            res = param.value
        else:
            res = param.value['value']

        param.delete()
        return res
