# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Pierre Verkest <pverkest@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy import Table, Column, ForeignKeyConstraint
from sqlalchemy.orm import (relationships, backref, relationship, base,
                            attributes)
from sqlalchemy.schema import Column as SA_Column
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import exc as sa_exc, util
from .field import Field, FieldException
from .mapper import ModelAdapter, ModelAttribute, ModelRepr
from anyblok.common import anyblok_column_prefix


class RelationshipProperty(relationships.RelationshipProperty):

    def __init__(self, *args, **kwargs):
        self.relationship_field = kwargs.pop('relationship_field')
        super(RelationshipProperty, self).__init__(*args, **kwargs)

    def _generate_backref(self):  # noqa
        """Interpret the 'backref' instruction to create a
        :func:`.relationship` complementary to this one."""

        if self.parent.non_primary:
            return
        if self.backref is not None and not self.back_populates:
            if isinstance(self.backref, util.string_types):
                backref_key, kwargs = self.backref, {}
            else:
                backref_key, kwargs = self.backref
            mapper = self.mapper.primary_mapper()

            check = set(mapper.iterate_to_root()).\
                union(mapper.self_and_descendants)
            for m in check:
                if m.has_property(backref_key):
                    raise sa_exc.ArgumentError(
                        "Error creating backref "
                        "'%s' on relationship '%s': property of that "
                        "name exists on mapper '%s'" %
                        (backref_key, self, m))

            # determine primaryjoin/secondaryjoin for the
            # backref.  Use the one we had, so that
            # a custom join doesn't have to be specified in
            # both directions.
            if self.secondary is not None:
                # for many to many, just switch primaryjoin/
                # secondaryjoin.   use the annotated
                # pj/sj on the _join_condition.
                pj = kwargs.pop(
                    'primaryjoin',
                    self._join_condition.secondaryjoin_minus_local)
                sj = kwargs.pop(
                    'secondaryjoin',
                    self._join_condition.primaryjoin_minus_local)
            else:
                pj = kwargs.pop(
                    'primaryjoin',
                    self._join_condition.primaryjoin_reverse_remote)
                sj = kwargs.pop('secondaryjoin', None)
                if sj:
                    raise sa_exc.InvalidRequestError(
                        "Can't assign 'secondaryjoin' on a backref "
                        "against a non-secondary relationship."
                    )

            foreign_keys = kwargs.pop('foreign_keys',
                                      self._user_defined_foreign_keys)
            parent = self.parent.primary_mapper()
            kwargs.setdefault('viewonly', self.viewonly)
            kwargs.setdefault('post_update', self.post_update)
            kwargs.setdefault('passive_updates', self.passive_updates)
            self.back_populates = backref_key
            _relationship = RelationshipProperty2(
                parent, self.secondary,
                pj, sj,
                foreign_keys=foreign_keys,
                back_populates=self.key,
                relationship_field=self.relationship_field,
                **kwargs)

            mapper._configure_property(backref_key, _relationship)

        if self.back_populates:
            self._add_reverse_property(self.back_populates)


def register_descriptor(class_, key, comparator=None,
                        parententity=None, doc=None, relationship_field=None):
    manager = base.manager_of_class(class_)
    descriptor = relationship_field.InstrumentedAttribute(
        class_, key, comparator=comparator, parententity=parententity,
        relationship_field=relationship_field)
    descriptor.__doc__ = doc
    manager.instrument_attribute(key, descriptor)
    return descriptor


class RelationshipProperty2(relationships.RelationshipProperty):

    def __init__(self, *args, **kwargs):
        self.relationship_field = kwargs.pop('relationship_field')
        super(RelationshipProperty2, self).__init__(*args, **kwargs)

    def instrument_class(self, mapper):
        register_descriptor(
            mapper.class_,
            self.key,
            comparator=self.comparator_factory(self, mapper),
            parententity=mapper,
            doc=self.doc,
            relationship_field=self.relationship_field,
        )


class RelationShipList:  # don't inherit list

    def append(self, x):
        res = super(RelationShipList, self).append(x)
        self.relationship_field_append_value(x)
        return res

    def extend(self, L):
        res = super(RelationShipList, self).extend(L)
        for el in L:
            self.relationship_field_append_value(el)

        return res

    def insert(self, i, x):
        res = super(RelationShipList, self).insert(i, x)
        self.relationship_field_append_value(x)
        return res

    def remove(self, x):
        self.relationship_field_remove_value(x)
        return super(RelationShipList, self).remove(x)

    def pop(self, *args, **kwargs):
        res = super(RelationShipList, self).pop(*args, **kwargs)
        self.relationship_field_remove_value(res)
        return res

    def clear(self):
        for x in self:
            self.relationship_field_remove_value(x)

        return super(RelationShipList, self).clear()


class RelationShip(Field):
    """ RelationShip class

    The RelationShip class is used to define the type of SQL field Declarations

    Add a new relation ship type::

        @Declarations.register(Declarations.RelationShip)
        class Many2one:
            pass

    the relationship column are forbidden because the model can be used on
    the model
    """

    def __init__(self, *args, **kwargs):
        self.forbid_instance(RelationShip)
        if 'model' in kwargs:
            self.model = ModelAdapter(kwargs.pop('model'))
        else:
            raise FieldException("model is required attribut")

        super(RelationShip, self).__init__(*args, **kwargs)

        if 'info' not in self.kwargs:
            self.kwargs['info'] = {}

        self.kwargs['info']['remote_model'] = self.model.model_name
        self.backref_properties = {}

    def autodoc_get_properties(self):
        res = super(RelationShip, self).autodoc_get_properties()
        res['model'] = self.model
        return res

    def apply_instrumentedlist(self, registry, namespace, fieldname):
        """ Add the InstrumentedList class to replace List class as result
        of the query

        :param registry: current registry
        """
        self.kwargs['collection_class'] = registry.InstrumentedList
        self.backref_properties['collection_class'] = registry.InstrumentedList

    def define_backref_properties(self, registry, namespace, properties):
        """ Add in the backref_properties, new property for the backref

        :param registry: current registry
        :param namespace: name of the model
        :param properties: properties known of the model
        """
        pass

    def format_backref(self, registry, namespace, fieldname, properties):
        """ Create the real backref, with the backref string and the
        backref properties

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        """
        _backref = self.kwargs.get('backref')
        if not _backref:
            return

        if isinstance(_backref, (list, tuple)):
            _backref, backref_properties = _backref
            self.backref_properties.update(backref_properties)

        self.define_backref_properties(registry, namespace, properties)

        if self.backref_properties:
            self.kwargs['backref'] = backref(_backref,
                                             **self.backref_properties)
            mapper = ModelAttribute(self.model.model_name, _backref)
            if not mapper.is_declared(registry):
                mapper.add_fake_relationship(registry, namespace, fieldname)

    def get_relationship_cls(self):
        return relationship

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        :rtype: sqlalchemy relation ship instance
        """
        self.model.check_model(registry)
        self.format_label(fieldname)
        self.kwargs['info']['label'] = self.label
        self.kwargs['info']['rtype'] = self.__class__.__name__
        self.apply_instrumentedlist(registry, namespace, fieldname)
        self.format_backref(registry, namespace, fieldname, properties)
        return self.get_relationship_cls()(
            self.model.tablename(registry), **self.kwargs)

    def must_be_declared_as_attr(self):
        """ Return True, because it is a relationship """
        return True

    def init_expire_attributes(self, registry, namespace, fieldname):
        """Init dict of expiration properties

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        """
        if namespace not in registry.expire_attributes:
            registry.expire_attributes[namespace] = {}

        if fieldname not in registry.expire_attributes[namespace]:
            registry.expire_attributes[namespace][fieldname] = set()


class RelationShipListMany2One:

    def relationship_field_append_value(self, value):
        for model_field, rfield in self.relationship_fied.link_between_columns:
            self.relationship_fied.apply_value_to(
                value, model_field, getattr(value, self.fieldname), rfield)

    def relationship_field_remove_value(self, value):
        for model_field, rfield in self.relationship_fied.link_between_columns:
            setattr(value, anyblok_column_prefix + model_field, None)


class Many2One(RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = Many2One(label="The relationship",
                                    model=Model.RemoteModel,
                                    remote_columns="The remote column",
                                    column_names="The column which have the "
                                                 "foreigh key",
                                    nullable=True,
                                    unique=False,
                                    one2many="themodels")

    If the ``remote_columns`` are not define then, the system takes the primary
    key of the remote model

    If the column doesn't exist, the column will be created. Use the
    nullable option.
    If the name is not filled, the name is "'remote table'_'remote colum'"

    :param model: the remote model
    :param remote_columns: the column name on the remote model
    :param column_names: the column on the model which have the foreign key
    :param nullable: If the column_names is nullable
    :param unique: If True, add the unique constraint on the column
    :param one2many: create the one2many link with this many2one
    """
    use_hybrid_property = True

    def __init__(self, **kwargs):
        super(Many2One, self).__init__(**kwargs)

        self._remote_columns = None
        if 'remote_columns' in kwargs:
            self._remote_columns = self.kwargs.pop('remote_columns')
            if not isinstance(self._remote_columns, (list, tuple)):
                self._remote_columns = [self._remote_columns]

        self.nullable = True
        if 'nullable' in kwargs:
            self.nullable = self.kwargs.pop('nullable')
            self.kwargs['info']['nullable'] = self.nullable

        self.unique = False
        if 'unique' in kwargs:
            self.unique = self.kwargs.pop('unique')
            self.kwargs['info']['unique'] = self.unique

        if 'one2many' in kwargs:
            self.kwargs['backref'] = self.kwargs.pop('one2many')
            self.kwargs['info']['remote_name'] = self.kwargs['backref']

        self._column_names = None
        if 'column_names' in kwargs:
            self._column_names = self.kwargs.pop('column_names')
            if not isinstance(self._column_names, (list, tuple)):
                self._column_names = [self._column_names]

        self.foreign_key_options = self.kwargs.pop('foreign_key_options', {})

    def autodoc_get_properties(self):
        res = super(Many2One, self).autodoc_get_properties()
        res['_remote_columns'] = self._remote_columns
        res['_column_names'] = self._column_names
        res['unique'] = self.unique
        return res

    def update_local_and_remote_columns_names(self, registry, namespace):
        if self._remote_columns is None:
            self.remote_columns = self.model.primary_keys(registry)
        else:
            self.remote_columns = [ModelAttribute(self.model.model_name, x)
                                   for x in self._remote_columns]

        self.kwargs['info']['remote_columns'] = [str(x)
                                                 for x in self.remote_columns]

        if self._column_names is None:
            model = ModelRepr(namespace)
            self.column_names = model.foreign_keys_for(
                registry, self.model.model_name)
            if not self.column_names:
                self.column_names = []
                for x in self.remote_columns:
                    cname = x.get_fk_name(registry).replace('.', '_')
                    self.column_names.append(ModelAttribute(namespace, cname))
        else:
            self.column_names = [ModelAttribute(namespace, x)
                                 for x in self._column_names]

    def add_expire_attributes(self, registry, namespace, fieldname, cname):
        self.init_expire_attributes(registry, namespace, cname)
        registry.expire_attributes[namespace][cname].add((fieldname,))
        if self.kwargs.get('backref'):
            backref = self.kwargs['backref']
            if isinstance(backref, (list, tuple)):
                backref = backref[0]

            registry.expire_attributes[namespace][cname].add(
                (fieldname, backref))

    def update_properties(self, registry, namespace, fieldname, properties):
        """ Create the column which has the foreign key if the column doesn't
        exist

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param propertie: the properties known
        """
        add_fksc = False
        self.link_between_columns = []
        self.model.check_model(registry)
        self.update_local_and_remote_columns_names(registry, namespace)
        if fieldname in [x.attribute_name for x in self.column_names]:
            raise FieldException("The column_names and the fieldname %r are "
                                 "the same, please choose another "
                                 "column_names" % fieldname)

        self.kwargs['info']['local_columns'] = ', '.join(
            str(x) for x in self.column_names)
        remote_types = {x.attribute_name: x.native_type(registry)
                        for x in self.remote_columns}
        remote_columns = {x.attribute_name: x
                          for x in self.remote_columns}
        for cname in self.column_names:
            if cname.is_declared(registry):
                del remote_types[cname.get_fk_column(registry)]

        col_names = []
        fk_names = []
        for cname in self.column_names:
            self.add_expire_attributes(registry, namespace, fieldname,
                                       cname.attribute_name)
            if not cname.is_declared(registry):
                rc, remote_type = self.get_column_information(
                    registry, cname, remote_types)
                cname.add_fake_column(registry)
                foreign_key = remote_columns[rc].get_fk_name(registry)
                self.create_column(cname, remote_type, foreign_key, properties)
                add_fksc = True
                fk_name = remote_columns[rc]
            else:
                fk_name = cname.get_fk_mapper(registry)

            col_names.append(cname.attribute_name)
            fk_names.append(fk_name.get_fk_name(registry))
            self.link_between_columns.append((cname.attribute_name,
                                              fk_name.attribute_name))

        if namespace == self.model.model_name:
            self.kwargs['remote_side'] = [
                properties[anyblok_column_prefix + x.attribute_name]
                for x in self.remote_columns]

        if (len(self.column_names) > 1 or add_fksc) and col_names and fk_names:
            properties['add_in_table_args'].append(
                ForeignKeyConstraint(col_names, fk_names,
                                     **self.foreign_key_options))

    def get_column_information(self, registry, cname, remote_types):
        if len(remote_types) == 1:
            rc = [x for x in remote_types][0]
            return rc, remote_types[rc]
        else:
            rc = cname.get_fk_column(registry)
            if rc is None:
                rc = cname.attribute_name[len(
                    self.model.tablename(registry)) + 1:]

            if rc in remote_types:
                return rc, remote_types[rc]
            else:
                cname.get_fk_column(registry)
                raise FieldException("Can not create the local "
                                     "column %r" % cname.attribute_name)

    def apply_instrumentedlist(self, registry, namespace, fieldname):
        """ Add the InstrumentedList class to replace List class as result
        of the query

        :param registry: current registry
        """
        properties = {
            'fieldname': fieldname, 'relationship_fied': self}
        InstrumentedList = type(
            'InstrumentedList', (RelationShipListMany2One, RelationShipList,
                                 registry.InstrumentedList), properties)
        self.backref_properties['collection_class'] = InstrumentedList

    def create_column(self, cname, remote_type, foreign_key, properties):

        def wrapper(cls):
            return SA_Column(
                cname.attribute_name,
                remote_type,
                nullable=self.nullable,
                unique=self.unique,
                info=dict(label=self.label, foreign_key=foreign_key))

        properties[(anyblok_column_prefix +
                    cname.attribute_name)] = declared_attr(wrapper)
        properties['loaded_columns'].append(cname.attribute_name)
        properties['hybrid_property_columns'].append(cname.attribute_name)
        properties[cname.attribute_name] = hybrid_property(
            self.wrap_getter_column(cname.attribute_name),
            super(Many2One, self).wrap_setter_column(cname.attribute_name),
            expr=self.wrap_expr_column(cname.attribute_name))

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Create the relationship

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param propertie: the properties known
        :rtype: Many2One relationship
        """
        self.kwargs['foreign_keys'] = '[%s]' % ', '.join(
            [x.get_fk_name(registry) for x in self.column_names])
        return super(Many2One, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)

    def apply_value_to(self, model_self, model_field, remote_self,
                       remote_field):
        if remote_self:
            value = getattr(remote_self,
                            anyblok_column_prefix + remote_field)
        else:
            value = None

        setattr(model_self, anyblok_column_prefix + model_field, value)

    def wrap_setter_column(self, fieldname):
        attr_name = anyblok_column_prefix + fieldname

        def setter_column(model_self, value):
            res = setattr(model_self, attr_name, value)
            for model_field, rfield in self.link_between_columns:
                self.apply_value_to(model_self, model_field, value, rfield)

            return res

        return setter_column


class InstrumentedAttribute_O2O(attributes.InstrumentedAttribute):

    def __init__(self, *args, **kwargs):
        self.relationship_field = kwargs.pop('relationship_field')
        super(InstrumentedAttribute_O2O, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        call_super = False
        if value:
            for cname, fname in self.relationship_field.link_between_columns:
                if instance:
                    if getattr(instance, fname):
                        setattr(value, cname, getattr(instance, fname))
                    else:
                        call_super = True
                else:
                    setattr(value, cname, instance)

        else:
            call_super = True

        if call_super:
            super(InstrumentedAttribute_O2O, self).__set__(instance, value)


class One2One(Many2One):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = One2One(label="The relationship",
                                   model=Model.RemoteModel,
                                   remote_columns="The remote column",
                                   column_names="The column which have the "
                                               "foreigh key",
                                   nullable=False,
                                   backref="themodels")

    If the remote_columns are not define then, the system take the primary key
    of the remote model

    If the column doesn't exist, then the column will be create. Use the
    nullable option.
    If the name is not filled then the name is "'remote table'_'remote colum'"

    :param model: the remote model
    :param remote_columns: the column name on the remote model
    :param column_names: the column on the model which have the foreign key
    :param nullable: If the column_names is nullable
    :param backref: create the one2one link with this one2one
    """

    InstrumentedAttribute = InstrumentedAttribute_O2O

    def __init__(self, **kwargs):
        super(One2One, self).__init__(**kwargs)

        if 'backref' not in kwargs:
            raise FieldException("backref is a required argument")

        if 'one2many' in kwargs:
            raise FieldException("Unknow argmument 'one2many'")

        self.kwargs['info']['remote_name'] = self.kwargs['backref']

    def define_backref_properties(self, registry, namespace, properties):
        """ Add option uselist = False

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param propertie: the properties known
        """
        self.backref_properties.update({'uselist': False})

    def apply_instrumentedlist(self, registry, namespace, fieldname):
        """ Add the InstrumentedList class to replace List class as result
        of the query

        :param registry: current registry
        """

    def get_relationship_cls(self):
        self.kwargs['relationship_field'] = self
        return RelationshipProperty


class Many2Many(RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = Many2Many(label="The relationship",
                                     model=Model.RemoteModel,
                                     join_table="many2many table",
                                     remote_columns="The remote column",
                                     m2m_remote_columns="Name in many2many"
                                     local_columns="local primary key"
                                     m2m_local_columns="Name in many2many"
                                     many2many="themodels")

    if the join_table is not defined, then the table join is
        "join\_'local table'_and\_'remote table'"

    .. warning::

        The join_table must be filled when the declaration of the
        Many2Many is done in a Mixin

    If the remote_columns are not define then, the system take the primary key
    of the remote model

    if the local_columns are not define the take the primary key of the local
        model

    :param model: the remote model
    :param join_table: the many2many table to join local and remote models
    :param remote_columns: the column name on the remote model
    :param m2m_remote_columns: the column name to remote model in m2m table
    :param local_columns: the column on the model
    :param m2m_local_columns: the column name to local model in m2m table
    :param many2many: create the opposite many2many on the remote model
    """

    def __init__(self, **kwargs):
        super(Many2Many, self).__init__(**kwargs)

        self.join_table = self.kwargs.pop('join_table', None)
        self.remote_columns = self.kwargs.pop('remote_columns', None)
        if self.remote_columns and not isinstance(self.remote_columns,
                                                  (list, tuple)):
            self.remote_columns = [self.remote_columns]

        self.m2m_remote_columns = self.kwargs.pop('m2m_remote_columns', None)
        if self.m2m_remote_columns and not isinstance(self.m2m_remote_columns,
                                                      (list, tuple)):
            self.m2m_remote_columns = [self.m2m_remote_columns]

        self.local_columns = self.kwargs.pop('local_columns', None)
        if self.local_columns and not isinstance(self.local_columns,
                                                 (list, tuple)):
            self.local_columns = [self.local_columns]

        self.m2m_local_columns = self.kwargs.pop('m2m_local_columns', None)
        if self.m2m_local_columns and not isinstance(self.m2m_local_columns,
                                                     (list, tuple)):
            self.m2m_local_columns = [self.m2m_local_columns]

        self.kwargs['backref'] = self.kwargs.pop('many2many', None)
        self.kwargs['info']['remote_name'] = self.kwargs['backref']

    def autodoc_get_properties(self):
        res = super(Many2Many, self).autodoc_get_properties()
        res['join table'] = self.join_table
        res['remote_columns'] = self.remote_columns
        res['m2m_remote_columns'] = self.m2m_remote_columns
        res['local_columns'] = self.local_columns
        res['m2m_local_columns'] = self.m2m_local_columns
        return res

    def get_m2m_columns(self, registry, columns, m2m_columns):
        if m2m_columns is None:
            m2m_columns = [x.get_fk_name(registry).replace('.', '_')
                           for x in columns]

        cols = []
        col_names = []
        ref_cols = []
        for i, column in enumerate(m2m_columns):
            sqltype = columns[i].native_type(registry)
            foreignkey = columns[i].get_fk_name(registry)
            cols.append(Column(column, sqltype, primary_key=True))
            col_names.append(column)
            ref_cols.append(foreignkey)

        return cols, ForeignKeyConstraint(col_names, ref_cols)

    def get_local_and_remote_columns(self, registry):
        if not self.local_columns:
            local_columns = self.local_model.primary_keys(registry)
        else:
            local_columns = [ModelAttribute(self.local_model.model_name, x)
                             for x in self.local_columns]

        if not self.remote_columns:
            remote_columns = self.model.primary_keys(registry)
        else:
            remote_columns = [ModelAttribute(self.model.model_name, x)
                              for x in self.remote_columns]

        self.kwargs['info']['local_columns'] = [x.attribute_name
                                                for x in local_columns]
        self.kwargs['info']['remote_columns'] = [x.attribute_name
                                                 for x in remote_columns]

        return local_columns, remote_columns

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Create the relationship

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param properties: the properties known
        :rtype: Many2One relationship
        """
        self.model.check_model(registry)
        self.local_model = ModelRepr(namespace)
        local_columns, remote_columns = self.get_local_and_remote_columns(
            registry)
        join_table = self.join_table
        if self.join_table is None:
            join_table = 'join_%s_and_%s' % (
                self.local_model.tablename(registry),
                self.model.tablename(registry))

        if join_table not in registry.declarativebase.metadata.tables:
            remote_columns, remote_fk = self.get_m2m_columns(
                registry, remote_columns, self.m2m_remote_columns)
            local_columns, local_fk = self.get_m2m_columns(
                registry, local_columns, self.m2m_local_columns)

            Table(join_table, registry.declarativebase.metadata, *(
                local_columns + remote_columns + [local_fk, remote_fk]))

        self.kwargs['secondary'] = join_table
        # definition of expiration
        if self.kwargs.get('backref'):
            self.init_expire_attributes(registry, namespace, fieldname)
            backref = self.kwargs['backref']
            if isinstance(backref, (tuple, list)):
                backref = backref[0]

            registry.expire_attributes[namespace][fieldname].add(
                ('x2m', fieldname, backref))
            model_name = self.model.model_name
            self.init_expire_attributes(registry, model_name, backref)
            registry.expire_attributes[model_name][backref].add(
                ('x2m', backref, fieldname))

        return super(Many2Many, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)


class InstrumentedAttribute_O2M(attributes.InstrumentedAttribute):

    def __init__(self, *args, **kwargs):
        self.relationship_field = kwargs.pop('relationship_field')
        super(InstrumentedAttribute_O2M, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        super(InstrumentedAttribute_O2M, self).__set__(instance, value)
        if instance:
            for cname, fname in self.relationship_field.link_between_columns:
                if value:
                    setattr(instance, cname, getattr(value, fname))
                else:
                    setattr(instance, cname, value)


class One2Many(RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = One2Many(label="The relationship",
                                    model=Model.RemoteModel,
                                    remote_columns="The remote column",
                                    primaryjoin="Join condition"
                                    many2one="themodel")

    If the primaryjoin is not filled then the join condition is
        "'local table'.'local promary key' == 'remote table'.'remote colum'"

    :param model: the remote model
    :param remote_columns: the column name on the remote model
    :param primaryjoin: the join condition between the remote column
    :param many2one: create the many2one link with this one2many
    """

    InstrumentedAttribute = InstrumentedAttribute_O2M

    def __init__(self, **kwargs):
        super(One2Many, self).__init__(**kwargs)

        self.remote_columns = None
        if 'remote_columns' in kwargs:
            remote_columns = self.kwargs.pop('remote_columns')
            if not isinstance(remote_columns, (list, tuple)):
                remote_columns = [remote_columns]

            self.remote_columns = [ModelAttribute(self.model.model_name, x)
                                   for x in remote_columns]

        if 'many2one' in kwargs:
            self.kwargs['backref'] = self.kwargs.pop('many2one')
            self.kwargs['info']['remote_names'] = self.kwargs['backref']

    def autodoc_get_properties(self):
        res = super(One2Many, self).autodoc_get_properties()
        res['remote_columns'] = self.remote_columns
        return res

    def find_foreign_key(self, registry, properties, tablename):
        """ Return the primary key come from the first step property

        :param registry: the registry which load the relationship
        :param properties: first step properties for the model
        :param tablename: the name of the table for the foreign key
        :rtype: column name of the primary key
        """
        fks = []
        for f, p in properties.items():
            if f == '__tablename__':
                continue

            if not hasattr(p, 'foreign_key'):
                continue

            if p.foreign_key:
                model = p.foreign_key.model_name
                if self.get_tablename(registry, model=model) == tablename:
                    fks.append(f)

        return fks

    def add_expire_attributes(self, registry, namespace, fieldname):
        if self.kwargs.get('backref'):
            backref = self.kwargs['backref']
            if isinstance(backref, (list, tuple)):
                backref = backref[0]

            model_name = self.model.model_name
            for rname in self.remote_columns:
                self.init_expire_attributes(
                    registry, model_name, rname.attribute_name)
                _rname = rname.attribute_name
                registry.expire_attributes[model_name][_rname].add((backref,))
                registry.expire_attributes[model_name][_rname].add(
                    (backref, fieldname))

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Create the relationship

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param propertie: the properties known
        :rtype: Many2One relationship
        """
        self.model.check_model(registry)
        if not self.remote_columns:
            self.remote_columns = self.model.foreign_keys_for(
                registry, namespace)

        self.kwargs['info']['remote_columns'] = [x.attribute_name
                                                 for x in self.remote_columns]

        self.link_between_columns = [
            (x.attribute_name, x.get_fk_mapper(registry).attribute_name)
            for x in self.remote_columns]

        if 'primaryjoin' not in self.kwargs:
            pjs = []
            for cname in self.remote_columns:
                pjs.append("%s == %s" % (
                    cname.get_fk_remote(registry),
                    cname.get_fk_name(registry)))

            # This must be a python and not a SQL AND cause of eval do
            # on the primaryjoin
            self.kwargs['primaryjoin'] = ' and '.join(pjs)

        self.add_expire_attributes(registry, namespace, fieldname)
        return super(One2Many, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)

    def define_backref_properties(self, registry, namespace, properties):
        """ Add option in the backref if both model and remote model are the
        same, it is for the One2Many on the same model

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param propertie: the properties known
        """
        if namespace == self.model.model_name:
            pks = ModelRepr(namespace).primary_keys(registry)
            self.backref_properties.update({'remote_side': [
                properties[anyblok_column_prefix + pk.attribute_name]
                for pk in pks]})

    def get_relationship_cls(self):
        self.kwargs['relationship_field'] = self
        return RelationshipProperty
