# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from sqlalchemy.schema import Column as SA_Column
from sqlalchemy.schema import ForeignKey


@Declarations.add_declaration_type()
class Column(Declarations.Field):
    """ Column class

    This class can't be instanciated
    """

    foreign_key = None
    sqlalchemy_type = None

    def __init__(self, *args, **kwargs):
        """ Initialize the column

        :param label: label of this field
        :type label: str
        """
        self.forbid_instance(Column)
        assert self.sqlalchemy_type

        if 'type_' in kwargs:
            del kwargs['type_']

        if 'foreign_key' in kwargs:
            model, col = kwargs.pop('foreign_key')
            if isinstance(model, str):
                self.foreign_key = model + '.' + col
            else:
                self.foreign_key = model.__tablename__ + '.' + col

        super(Column, self).__init__(*args, **kwargs)

    def native_type(cls):
        """ Return the native SqlAlchemy type """
        return cls.sqlalchemy_type

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: known properties of the model
        :rtype: sqlalchemy column instance
        """
        self.format_label(fieldname)
        args = self.args

        kwargs = self.kwargs.copy()
        if 'info' not in kwargs:
            kwargs['info'] = {}

        kwargs['info']['label'] = self.label

        if self.foreign_key:
            args = args + (ForeignKey(self.foreign_key),)
            kwargs['info']['foreign_key'] = self.foreign_key

        return SA_Column(fieldname, self.sqlalchemy_type, *args, **kwargs)
