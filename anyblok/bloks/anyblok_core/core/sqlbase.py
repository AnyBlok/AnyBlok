# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from ..exceptions import SqlBaseException
from sqlalchemy.orm import aliased, ColumnProperty
from sqlalchemy.sql.expression import true
from sqlalchemy.sql import functions
from sqlalchemy import or_, and_


def query_method(name):
    """ Apply a wrapper on a method name and return the classmethod of
    wrapper for this name
    """

    def wrapper(cls, query, *args, **kwargs):
        return query.sqlalchemy_query_method(name, *args, **kwargs)

    return classmethod(wrapper)


class SqlMixin:

    @classmethod
    def query(cls, *elements):
        """ Facility to do a SqlAlchemy query::

            query = MyModel.query()

        is equal at::

            query = self.registry.session.query(MyModel)

        :param elements: pass at the SqlAlchemy query, if the element is a
        string then thet are see as field of the model
        :rtype: SqlAlchemy Query
        """
        res = []
        for f in elements:
            if isinstance(f, str):
                res.append(getattr(cls, f))
            else:
                res.append(f)

        if res:
            return cls.registry.query(*res)

        return cls.registry.query(cls)

    is_sql = True

    @classmethod
    def get_on_model_methods(cls):
        return ['update', 'delete']

    @classmethod
    def aliased(cls, *args, **kwargs):
        """ Facility to Apply an aliased on the model::

            MyModelAliased = MyModel.aliased()

        is equal at::

            from sqlalchemy.orm import aliased
            MyModelAliased = aliased(MyModel)

        :rtype: SqlAlchemy aliased of the model
        """
        return aliased(cls, *args, **kwargs)

    @classmethod
    def get_where_clause_from_primary_keys(cls, **pks):
        """ return the where clause to find object from pks

        :param \*\*pks: dict {primary_key: value, ...}
        :rtype: where clause
        :exception: SqlBaseException
        """
        _pks = cls.get_primary_keys()
        for pk in _pks:
            if pk not in pks:
                raise SqlBaseException("No primary key %s filled for %r" % (
                    pk, cls.__registry_name__))

        return [getattr(cls, k) == v for k, v in pks.items()]

    @classmethod
    def from_primary_keys(cls, **pks):
        """ return the instance of the model from the primary keys

        :param \*\*pks: dict {primary_key: value, ...}
        :rtype: instance of the model
        """
        where_clause = cls.get_where_clause_from_primary_keys(**pks)
        query = cls.query().filter(*where_clause)
        if query.count():
            return query.first()

        return None

    @classmethod
    def from_multi_primary_keys(cls, *pks):
        """ return the instances of the model from the primary keys

        :param \*pks: list of dict [{primary_key: value, ...}]
        :rtype: instances of the model
        """
        where_clause = []
        for _pks in pks:
            where_clause.append(cls.get_where_clause_from_primary_keys(**_pks))

        if not where_clause:
            return []

        where_clause = or_(*[and_(*x) for x in where_clause])

        query = cls.query().filter(where_clause)
        if query.count():
            return query.all()

        return []

    def to_primary_keys(self):
        """ return the primary keys and values for this instance

        :rtype: dict {primary key: value, ...}
        """
        pks = self.get_primary_keys()
        return {x: getattr(self, x) for x in pks}

    @classmethod
    def get_primary_keys(cls):
        """ return the name of the primary keys of the model

        :type: list of the primary keys name
        """
        Column = cls.registry.System.Column
        model = cls.__registry_name__
        query = Column.query()
        query = query.filter(Column.model == model)
        query = query.filter(Column.primary_key == true())
        return query.all().name

    @Declarations.classmethod_cache()
    def _fields_description(cls):
        """ Return the information of the Field, Column, RelationShip """
        Field = cls.registry.System.Field
        Column = cls.registry.System.Column
        RelationShip = cls.registry.System.RelationShip

        def get_query(Model):
            columns = [
                Model.name.label('id'),
                Model.label,
                Model.ftype.label('type'),
            ]
            if Model is Column:
                columns.append(Model.nullable)
                columns.append(Model.primary_key)
                columns.append(Model.remote_model.label('model'))
            elif Model is RelationShip:
                columns.append(Model.nullable)
                columns.append(functions.literal_column('false').label(
                    'primary_key'))
                columns.append(Model.remote_model.label('model'))
            elif Model is Field:
                columns.append(
                    functions.literal_column('true as nullable'))
                columns.append(functions.literal_column('false').label(
                    'primary_key'))
                columns.append(functions.literal_column('null').label(
                    'model'))

            return Model.query(*columns).filter(
                Model.model == cls.__registry_name__)

        query = get_query(RelationShip).union_all(get_query(Column)).union_all(
            get_query(Field))
        fields2get = [x['name'] for x in query.column_descriptions]
        return {x.id: {y: getattr(x, y) for y in fields2get}
                for x in query.all()}

    @classmethod
    def fields_description(cls, fields=None):
        res = cls._fields_description()
        if fields:
            return {x: y for x, y in res.items() if x in fields}

        return res

    def to_dict(self, *fields, **related_fields):
        """ Transform a record to the dict of value

        :param fields: list of fields to put in dict, if not selected fields
            them take all
        :rtype: dict
        """

        if not fields:
            fields = self.__class__.fields_description().keys()

        model = self.__class__

        result = {}

        for field in fields:
            field_value, field_property = getattr(self, field), getattr(model, field).property
            if field_value is None or type(field_property) == ColumnProperty:
                # If value is None, then do not go any further whatever the column property tells you.
                result[field] = field_value
            else:
                field_related_fields = related_fields.get(field)
                if not field_related_fields:
                    field_related_fields = field_property.mapper.entity.get_primary_keys
                    sub_related_fields = {}
                else:
                    sub_related_fields = {e[0]: e[1] for e in field_related_fields if (type(e) == tuple and len(e) == 2)}
                    field_related_fields = [e[0] if type(e) == tuple else e for e in field_related_fields]
                if field_property.uselist:
                    result[field] = [r.to_dict(*field_related_fields, **sub_related_fields) for r in field_value]
                else:
                    result[field] = field_value.to_dict(*field_related_fields, **sub_related_fields)

        return result


@Declarations.register(Declarations.Core)
class SqlBase(SqlMixin):
    """ this class is inherited by all the SQL model
    """

    sqlalchemy_query_delete = query_method('delete')
    sqlalchemy_query_update = query_method('update')

    def update(self, *args, **kwargs):
        """ Call the SqlAlchemy Query.update method on the instance of the
        model::

            self.update({...})

        is equal at::

            query = self.registry.session.query(MyModel)
            query = query.filter(MyModel.``pk`` == self.``pk``)
            query.update({...})

        """
        pks = self.get_primary_keys()
        where_clause = [getattr(self.__class__, pk) == getattr(self, pk)
                        for pk in pks]
        self.__class__.query().filter(*where_clause).update(*args, **kwargs)

    def delete(self):
        """ Call the SqlAlchemy Query.delete method on the instance of the
        model::

            self.delete()

        is equal at::

            query = self.registry.session.query(MyModel)
            query = query.filter(MyModel.``pk`` == self.``pk``)
            query.delete()

        """
        pks = self.get_primary_keys()
        where_clause = [getattr(self.__class__, pk) == getattr(self, pk)
                        for pk in pks]
        self.__class__.query().filter(*where_clause).delete()

    @classmethod
    def insert(cls, **kwargs):
        """ Insert in the table of the model::

            MyModel.insert(...)

        is equal at::

            mymodel = MyModel(...)
            MyModel.registry.session.add(mymodel)
            MyModel.registry.session.flush()

        """
        instance = cls(**kwargs)
        cls.registry.add(instance)
        cls.registry.flush()
        return instance

    @classmethod
    def multi_insert(cls, *args):
        """ Insert in the table one or more entry of the model::

            MyModel.multi_insert([{...}, ...])

        the flush will be done only one time at the end of the insert

        :exception: SqlBaseException
        """
        instances = []
        for kwargs in args:
            if not isinstance(kwargs, dict):
                raise SqlBaseException("multi_insert method wait list of dict")

            instance = cls(**kwargs)
            cls.registry.add(instance)
            instances.append(instance)

        if instances:
            cls.registry.flush()

        return instances

    @classmethod
    def precommit_hook(cls, method, put_at_the_end_if_exist=False):
        """ Same in the registry a hook to call just before the commit

        .. warning:: Only one instance of the hook is called before the commit

        :param method: the method to call on this model
        put_at_the_end_if_exist: If ``True`` the hook is move at the end
        """
        cls.registry.precommit_hook(cls.__registry_name__, method,
                                    put_at_the_end_if_exist)
