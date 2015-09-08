# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.declarations import Declarations, classmethod_cache
from anyblok.field import FieldException
from ..exceptions import SqlBaseException
from sqlalchemy.orm import aliased, ColumnProperty
from sqlalchemy.sql.expression import true
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
    def define_table_args(cls):
        return ()

    @classmethod
    def define_mapper_args(cls):
        return {}

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

    @classmethod_cache()
    def _fields_description(cls):
        """ Return the information of the Field, Column, RelationShip """
        Field = cls.registry.System.Field
        query = Field.query().filter(Field.model == cls.__registry_name__)
        return {x.name: x._description() for x in query.all()}

    @classmethod
    def fields_description(cls, fields=None):
        res = cls._fields_description()
        if fields:
            return {x: y for x, y in res.items() if x in fields}

        return res

    def _format_field(self, field):
        related_fields = None
        if isinstance(field, (tuple, list)):
            if len(field) == 1:
                related_fields = ()
            elif len(field) == 2:
                related_fields = field[1]
                if related_fields is None:
                    related_fields = ()
                elif not isinstance(related_fields, (tuple, list)):
                    raise SqlBaseException("%r the related fields wanted "
                                           "must be a tuple or empty or "
                                           "None value" % related_fields)
            else:
                raise SqlBaseException("%r the number of argument is "
                                       "wrong, waiting 1 or 2 arguments "
                                       "(name of the relation[, (related "
                                       "fields)])" % (field,))

            field = field[0]

        return field, related_fields

    def to_dict(self, *fields):
        """ Transform a record to the dict of value

        :param fields: list of fields to put in dict; if not selected, fields
            then take them all. A field is either one of these:

                * a string (which is the name of the field)
                * a 2-tuple if the field is a relationship (name of the field,
                  tuple of foreign model fields)

        :rtype: dict

        Here are some examples::

            =>> instance.to_dict()  # get all fields
            {"id": 1,
             "column1": "value 1",
             "column2": "value 2",
             "column3": "value 3",
             "relation1": {"relation_pk_1": 42, "relation_pk_2": "also 42"}
                                            # m2o or o2o : this is a dictionary
             "relation2": [{"id": 28}, {"id": 1}, {"id": 34}]
                                # o2m or m2m : this is a list of dictionaries
             }

            =>> instance.to_dict("column1", "column2", "relation1")
                        # get selected fields only (without any constraints)
            {"column1": "value 1",
             "column2": "value 2",
             "relation1": {"relation_pk_1": 42, "relation_pk_2": "also 42"}
             }

            =>> instance.to_dict("column1", "column2", (
                        # select fields to use in the relation related model
                "relation1", ("relation_pk1", "name", "value")
                            # there is no constraints in the choice of fields
                ))
            {"column1": "value",
             "column2": "value",
             "relation1": {"relation_pk_1": 42, "name": "H2G2", "value": "42"}
             }

            =>> instance.to_dict("column1", "column2", ("relation1", ))
            # or
            =>> instance.to_dict("column1", "column2", ("relation1", None))
            # or
            =>> instance.to_dict("column1", "column2", ("relation1", ()))
                                  # select all the fields of the relation ship
            {"column1": "value",
             "column2": "value",
             "relation1": {"relation_pk_1": 42, "name": "H2G2", "value": "42"}
             }

            =>> instance.to_dict("column1", "column2", (
                                        # select relation fields recursively
                "relation1", ("name", "value", (
                    "relation", ("a", "b", "c")
                    ))
                ))
            {"column1": "value",
             "column2": "value",
             "relation1": {"name": "H2G2", "value": "42", "relation": [
                 {"a": 10, "b": 20, "c": 30},
                 {"a": 11, "b": 22, "c": 33},
                 ]}
             }
        """
        result = {}
        cls = self.__class__
        fields = fields if fields else cls.fields_description().keys()

        for field in fields:
            # if field is ("relation_name", ("list", "of", "relation",
            # "fields")), deal with it.
            field, related_fields = self._format_field(field)
            # Get the actual data
            field_value, field_property = getattr(self, field), None
            try:
                field_property = getattr(getattr(cls, field), 'property', None)
            except FieldException:
                pass

            # Deal with this data
            if field_property is None:
                # it is the case of field function (hyprid property)
                result[field] = field_value
            elif field_value is None or type(field_property) == ColumnProperty:
                # If value is None, then do not go any further whatever
                # the column property tells you.
                result[field] = field_value
            else:
                # it is should be RelationshipProperty
                if related_fields is None:
                    # If there is no field list to the relation,
                    # use only primary keys
                    related_fields = field_property.mapper.entity
                    related_fields = related_fields.get_primary_keys()
                # One2One, One2Many, Many2One or Many2Many ?
                if field_property.uselist:
                    result[field] = [r.to_dict(*related_fields)
                                     for r in field_value]
                else:
                    result[field] = field_value.to_dict(*related_fields)

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
        return self.__class__.query().filter(*where_clause).update(
            *args, **kwargs)

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
        instances = cls.registry.InstrumentedList()
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
    def precommit_hook(cls, method, *args, **kwargs):
        """ Same in the registry a hook to call just before the commit

        .. warning:: Only one instance of the hook is called before the commit

        :param method: the method to call on this model
        :param put_at_the_end_if_exist: If ``True`` the hook is move at the end
        """
        cls.registry.precommit_hook(
            cls.__registry_name__, method, *args, **kwargs)
