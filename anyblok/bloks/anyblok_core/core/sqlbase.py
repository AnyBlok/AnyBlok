# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.declarations import Declarations, classmethod_cache
from anyblok.field import FieldException
from anyblok.column import Column
from anyblok.mapper import FakeColumn, FakeRelationShip
from anyblok.relationship import RelationShip, Many2Many
from anyblok.common import anyblok_column_prefix
from ..exceptions import SqlBaseException
from sqlalchemy.orm import aliased, ColumnProperty, load_only
from sqlalchemy.sql.expression import true
from sqlalchemy import or_, and_, inspect
from sqlalchemy_utils.models import NO_VALUE, NOT_LOADED_REPR
from sqlalchemy.orm.session import object_state
from sqlalchemy import delete, select, update as sqla_update


class uniquedict(dict):

    def add_in_res(self, key, attrs):
        if key not in self:
            self[key] = []

        for attr in attrs:
            if attr not in self[key]:
                self[key].append(attr)


class SqlMixin:

    __db_schema__ = None

    def __repr__(self):
        state = inspect(self)
        field_reprs = []
        fields_description = self.fields_description()
        keys = list(fields_description.keys())
        keys.sort()
        for key in keys:
            type_ = fields_description[key]['type']
            if key in state.attrs:
                value = state.attrs.get(key).loaded_value
            elif (anyblok_column_prefix + key) in state.attrs:
                value = state.attrs.get(
                    anyblok_column_prefix + key).loaded_value
            else:
                continue  # pragma: no cover

            if value == NO_VALUE:
                value = NOT_LOADED_REPR
            elif value and type_ in ('One2Many', 'Many2Many'):
                value = '<%s len(%d)>' % (
                    fields_description[key]['model'],
                    len(value)
                )
            elif value and type_ in ('One2One', 'Many2One'):
                value = '<%s(%s)>' % (
                    fields_description[key]['model'],
                    ', '.join(['='.join([x, str(y)])
                               for x, y in value.to_primary_keys().items()])
                )
            else:
                value = repr(value)

            field_reprs.append('='.join((key, value)))

        return '<%s(%s)>' % (
            self.__class__.__registry_name__, ', '.join(field_reprs)
        )

    @classmethod
    def define_table_args(cls):
        return ()

    @classmethod
    def define_table_kwargs(cls):
        res = {}
        if cls.__db_schema__ is not None:
            res.update({'schema': cls.__db_schema__})

        return res

    @classmethod
    def define_mapper_args(cls):
        return {}

    @classmethod
    def get_all_registry_names(cls):
        models = list(cls.__depends__)
        models.insert(0, cls.__registry_name__)
        return models

    @classmethod
    def query(cls, *elements):
        """ Facility to do a SqlAlchemy query::

            query = MyModel.query()

        is equal at::

            query = self.anyblok.session.query(MyModel)

        :param elements: pass at the SqlAlchemy query, if the element is a
                         string then thet are see as field of the model
        :rtype: SqlAlchemy Query
        """
        res = []
        for f in elements:
            if isinstance(f, str):
                res.append(getattr(cls, f).label(f))
            else:
                res.append(f)

        if res:
            query = cls.anyblok.query(*res)
        else:
            query = cls.anyblok.query(cls)

        query.set_Model(cls)
        return query

    @classmethod
    def execute_sql_statement(cls, *args, **kwargs):
        """call SqlA execute method on the session"""
        return cls.anyblok.execute(*args, **kwargs)

    @classmethod
    def select_sql_statement(cls, *elements):
        """ Facility to do a SqlAlchemy query::

            stmt = MyModel.select()

        is equal at::

            from anyblok import select

            stmt = select(MyModel)

        but select can be overload by model and it is
        possible to apply whereclause or anything matter

        :param elements: pass at the SqlAlchemy query, if the element is a
                         string then thet are see as field of the model
        :rtype: SqlAlchemy Query
        """
        res = []
        for f in elements:
            if isinstance(f, str):
                res.append(getattr(cls, f).label(f))
            else:
                res.append(f)

        if res:
            stmt = select(*res)
        else:
            stmt = select(cls)

        return cls.default_filter_on_sql_statement(stmt)

    @classmethod
    def default_filter_on_sql_statement(cls, statement):
        return statement

    is_sql = True

    @classmethod
    def aliased(cls, *args, **kwargs):
        """ Facility to Apply an aliased on the model::

            MyModelAliased = MyModel.aliased()

        is equal at::

            from sqlalchemy.orm import aliased
            MyModelAliased = aliased(MyModel)

        :rtype: SqlAlchemy aliased of the model
        """
        alias = aliased(cls, *args, **kwargs)
        alias.anyblok = cls.anyblok
        return alias

    @classmethod
    def get_where_clause_from_primary_keys(cls, **pks):
        """ return the where clause to find object from pks

        :param _*_*pks: dict {primary_key: value, ...}
        :rtype: where clause
        :exception: SqlBaseException
        """
        _pks = cls.get_primary_keys()
        for pk in _pks:
            if pk not in pks:  # pragma: no cover
                raise SqlBaseException("No primary key %s filled for %r" % (
                    pk, cls.__registry_name__))

        return [getattr(cls, k) == v for k, v in pks.items()]

    @classmethod
    def query_from_primary_keys(cls, **pks):
        """return a Query object in order to get object from primary keys.

        .. code::

            query = Model.query_from_primary_keys(**pks)
            obj = query.one()

        :param _*_*pks: dict {primary_key: value, ...}
        :rtype: Query object
        """
        where_clause = cls.get_where_clause_from_primary_keys(**pks)
        return cls.query().filter(*where_clause)

    @classmethod
    def from_primary_keys(cls, **pks):
        """ return the instance of the model from the primary keys

        :param **pks: dict {primary_key: value, ...}
        :rtype: instance of the model
        """
        query = cls.query_from_primary_keys(**pks)
        return query.one_or_none()

    @classmethod
    def from_multi_primary_keys(cls, *pks):
        """ return the instances of the model from the primary keys

        :param _*pks: list of dict [{primary_key: value, ...}]
        :rtype: instances of the model
        """
        where_clause = []
        for _pks in pks:
            where_clause.append(cls.get_where_clause_from_primary_keys(**_pks))

        if not where_clause:
            return []

        where_clause = or_(*[and_(*x) for x in where_clause])

        query = cls.query().filter(where_clause)
        return query.all()

    def to_primary_keys(self):
        """ return the primary keys and values for this instance

        :rtype: dict {primary key: value, ...}
        """
        pks = self.get_primary_keys()
        return {x: getattr(self, x) for x in pks}

    @classmethod_cache()
    def get_primary_keys(cls):
        """ return the name of the primary keys of the model

        :type: list of the primary keys name
        """
        C = cls.anyblok.System.Column
        query = C.query()
        query = query.options(load_only(C.name))
        query = query.filter(C.model.in_(cls.get_all_registry_names()))
        query = query.filter(C.primary_key == true())
        # DISTINCT does not works on MySQL/MsSQL
        return list(set(query.all().name))

    @classmethod_cache()
    def _fields_description(cls):
        """ Return the information of the Field, Column, RelationShip """
        Field = cls.anyblok.System.Field
        res = {}
        for registry_name in cls.__depends__:
            query = Field.query().filter(Field.model == registry_name)
            res.update({x.name: x._description() for x in query.all()})

        query = Field.query().filter(Field.model == cls.__registry_name__)
        res.update({x.name: x._description() for x in query.all()})
        return res

    @classmethod
    def fields_description(cls, fields=None):
        res = cls._fields_description()
        if fields:
            return {x: y for x, y in res.items() if x in fields}

        return res

    @classmethod_cache()
    def get_hybrid_property_columns(cls):
        """Return the hybrid properties columns name from the Model and the
        inherited model if they come from polymorphisme
        """
        hybrid_property_columns = cls.hybrid_property_columns
        if 'polymorphic_identity' in cls.__mapper_args__:
            pks = cls.get_primary_keys()
            fd = cls.fields_description(pks)
            for pk in pks:
                if fd[pk].get('model'):  # pragma: no cover
                    Model = cls.anyblok.get(fd[pk]['model'])
                    hybrid_property_columns.extend(
                        Model.get_hybrid_property_columns())

        return hybrid_property_columns

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
            except FieldException:  # pragma: no cover
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

    @classmethod_cache()
    def getFieldType(cls, name):
        """Return the type of the column

        ::

            TheModel.getFieldType(nameOfTheColumn)

        this method take care if it is a polymorphic model or not

        :param name: name of the column
        :rtype: String, the name of the Type of column used
        """
        Field = cls.anyblok.System.Field
        query = Field.query()
        query = query.filter(Field.name == name)
        query = query.filter(Field.model.in_(cls.get_all_registry_names()))
        query = query.limit(1)
        return query.one().ftype

    @classmethod_cache()
    def find_remote_attribute_to_expire(cls, *fields):
        res = uniquedict()
        _fields = []
        _fields.extend(fields)
        model = get_model_information(cls.anyblok, cls.__registry_name__)
        while _fields:
            field = _fields.pop()
            field = field if isinstance(field, str) else field.name
            _field = model[field]

            if isinstance(_field, (Column, FakeColumn)):
                _fields.extend(x for x, y in model.items()
                               if (isinstance(y, RelationShip) and
                                   not isinstance(y, Many2Many))
                               for mapper in y.column_names
                               if mapper.attribute_name == field)
                if (
                    isinstance(_field, Column) and _field.foreign_key
                ):  # pragma: no cover
                    rmodel = cls.anyblok.loaded_namespaces_first_step[
                        _field.foreign_key.model_name]
                    for rc in [x for x, y in rmodel.items()
                               if isinstance(y, RelationShip)
                               for mapper in y.remote_columns
                               if mapper.attribute_name == field]:
                        rfield = rmodel[rc]
                        if isinstance(rfield, FakeRelationShip):
                            res.add_in_res(rfield.mapper.attribute_name, [rc])
                        elif (isinstance(rfield, RelationShip) and
                              'backref' in rfield.kwargs):
                            res.add_in_res(
                                rfield.kwargs['backref'][0], [rc])

            elif (isinstance(_field, RelationShip) and
                  not isinstance(_field, Many2Many) and
                  'backref' in _field.kwargs):
                res.add_in_res(field, [_field.kwargs['backref'][0]])
            elif isinstance(_field, FakeRelationShip):  # pragma: no cover
                res.add_in_res(field, [_field.mapper.attribute_name])

        return res

    @classmethod_cache()
    def find_relationship(cls, *fields):
        """ Find column and relation ship link with the column or relationship
        passed in fields.

        :param _*fields: lists of the attribute name
        :rtype: list of the attribute name of the attribute and relation ship
        """
        res = []
        _fields = []
        _fields.extend(fields)
        model = get_model_information(cls.anyblok, cls.__registry_name__)
        while _fields:
            field = _fields.pop()
            if not isinstance(field, str):
                field = field.name  # pragma: no cover

            if field in res:
                continue

            _field = model[field]
            res.append(field)
            if isinstance(_field, (Column, FakeColumn)):
                _fields.extend(x
                               for x, y in model.items()
                               if (isinstance(y, RelationShip) and
                                   not isinstance(y, Many2Many))
                               for mapper in y.column_names
                               if mapper.attribute_name == field)
            elif (isinstance(_field, RelationShip) and
                  not isinstance(_field, Many2Many)):
                for mapper in _field.column_names:
                    _fields.append(mapper.attribute_name)

        return res


def get_model_information(anyblok, registry_name):
    model = anyblok.loaded_namespaces_first_step[registry_name]
    for depend in model['__depends__']:
        if depend != registry_name:
            for x, y in get_model_information(anyblok, depend).items():
                if x not in model:
                    model[x] = y  # pragma: no cover

    return model


@Declarations.register(Declarations.Core)
class SqlBase(SqlMixin):
    """ this class is inherited by all the SQL model
    """

    def get_modified_fields(self):
        """return the fields which have changed and their previous values"""
        state = object_state(self)
        modified_fields = {}
        for attr in state.manager.attributes:
            if not hasattr(attr.impl, 'get_history'):
                continue  # pragma: no cover

            added, unmodified, deleted = attr.impl.get_history(
                state, state.dict)

            if added or deleted:
                field = attr.key
                if field.startswith(anyblok_column_prefix):
                    field = field[len(anyblok_column_prefix):]

                modified_fields[field] = deleted[0] if deleted else None

        return modified_fields

    def expire_relationship_mapped(self, mappers):
        """ Expire the objects linked with this object, in function of
        the mappers definition
        """
        for field_name, rfields in mappers.items():
            fields = getattr(self, field_name)
            if not isinstance(fields, list):
                fields = [fields]

            for field in fields:
                if field is not None:
                    field.expire(*rfields)

    def refresh(self, *fields, with_for_update=None):
        """ Expire and reload all the attribute of the instance

        See: http://docs.sqlalchemy.org/en/latest/orm/session_api.html
        #sqlalchemy.orm.session.Session.refresh
        """
        self.anyblok.refresh(self, fields, with_for_update=with_for_update)

    def expunge(self):
        """Expunge the instance in the session"""
        self.anyblok.session.expunge(self)

    def expire(self, *fields):
        """ Expire the attribute of the instance, theses attributes will be
        load at the next  call of the instance

        see: http://docs.sqlalchemy.org/en/latest/orm/session_api.html
        #sqlalchemy.orm.session.Session.expire
        """
        self.anyblok.expire(self, fields)

    def flag_modified(self, *fields):
        """ Flag the attributes as modified

        see: http://docs.sqlalchemy.org/en/latest/orm/session_api.html
        #sqlalchemy.orm.session.Session.expire
        """
        self.anyblok.flag_modified(self, fields)

    @classmethod
    def delete_sql_statement(cls):
        """Return a statement to delete some element"""
        return cls.default_filter_on_sql_statement(delete(cls))

    def delete(self, byquery=False, flush=True):
        """ Call the SqlAlchemy Query.delete method on the instance of the
        model::

            self.delete()

        is equal at::

            flush the session
            remove the instance of the session
            and expire all the session, to reload the relation ship

        """
        if byquery:
            cls = self.__class__
            self.execute_sql_statement(
                delete(cls).where(
                    *cls.get_where_clause_from_primary_keys(
                        **self.to_primary_keys())))
            self.expunge()
        else:
            model = self.anyblok.loaded_namespaces_first_step[
                self.__registry_name__]
            fields = model.keys()
            mappers = self.__class__.find_remote_attribute_to_expire(*fields)
            self.expire_relationship_mapped(mappers)
            self.anyblok.session.delete(self)

        if flush:
            self.anyblok.flush()

    @classmethod
    def update_sql_statement(cls):
        return cls.default_filter_on_sql_statement(sqla_update(cls))

    def update(self, byquery=False, flush=False, **values):
        """ Hight livel method to update the session for the instance
        ::

            self.update(val1=.., val2= ...)

        ..warning::

            the columns and values is passed as named arguments to show
            a difference with Query.update meth

        """
        if byquery:
            cls = self.__class__
            return self.execute_sql_statement(
                sqla_update(cls).where(
                    *cls.get_where_clause_from_primary_keys(
                        **self.to_primary_keys())).values(**values)).rowcount

        for x, v in values.items():
            setattr(self, x, v)

        if flush:
            self.anyblok.flush()  # pragma: no cover

        return 1 if values else 0

    @classmethod
    def insert(cls, **kwargs):
        """ Insert in the table of the model::

            MyModel.insert(...)

        is equal at::

            mymodel = MyModel(...)
            MyModel.anyblok.session.add(mymodel)
            MyModel.anyblok.flush()

        """
        instance = cls(**kwargs)
        cls.anyblok.add(instance)
        cls.anyblok.flush()
        return instance

    @classmethod
    def multi_insert(cls, *args):
        """ Insert in the table one or more entry of the model::

            MyModel.multi_insert([{...}, ...])

        the flush will be done only one time at the end of the insert

        :exception: SqlBaseException
        """
        instances = cls.anyblok.InstrumentedList()
        for kwargs in args:
            if not isinstance(kwargs, dict):  # pragma: no cover
                raise SqlBaseException("multi_insert method wait list of dict")

            instance = cls(**kwargs)
            cls.anyblok.add(instance)
            instances.append(instance)

        if instances:
            cls.anyblok.flush()

        return instances
