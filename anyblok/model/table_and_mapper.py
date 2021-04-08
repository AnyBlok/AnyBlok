# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .plugins import ModelPluginBase
from .exceptions import ModelException
from sqlalchemy import ForeignKeyConstraint, CheckConstraint
from sqlalchemy.ext.declarative import declared_attr
from ..common import sgdb_in


class TableMapperPlugin(ModelPluginBase):

    def initialisation_tranformation_properties(self, properties,
                                                transformation_properties):
        """ Initialise the transform properties: hybrid_method

        :param new_type_properties: param to add in a new base if need
        """
        properties['add_in_table_args'] = []
        if 'table_args' not in transformation_properties:
            transformation_properties['table_args'] = False
            transformation_properties['table_kwargs'] = False
        if 'mapper_args' not in transformation_properties:
            transformation_properties['mapper_args'] = False

    def transform_base(self, namespace, base,
                       transformation_properties,
                       new_type_properties):
        """Test if define_table/mapper_args are in the base, and call them
        save the value in the properties

        if  __table/mapper_args__ are in the base then raise ModelException

        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param transformation_properties: the properties of the model
        :param new_type_properties: param to add in a new base if need
        """
        if hasattr(base, '__table_args__'):
            raise ModelException(
                "'__table_args__' attribute is forbidden, on Model : %r (%r)."
                "Use the class method 'define_table_args' to define the value "
                "allow anyblok to fill his own '__table_args__' attribute" % (
                    namespace, base.__table_args__))

        if hasattr(base, '__mapper_args__'):
            raise ModelException(
                "'__mapper_args__' attribute is forbidden, on Model : %r (%r)."
                "Use the class method 'define_mapper_args' to define the "
                "value allow anyblok to fill his own '__mapper_args__' "
                "attribute" % (namespace, base.__mapper_args__))

        if hasattr(base, 'define_table_args'):
            transformation_properties['table_args'] = True

        if hasattr(base, 'define_table_kwargs'):
            transformation_properties['table_kwargs'] = True

        if hasattr(base, 'define_mapper_args'):
            transformation_properties['mapper_args'] = True

    def insert_in_bases(self, new_base, namespace, properties,
                        transformation_properties):
        """ Create overwrite to define table and mapper args to define some
        options for SQLAlchemy

        :param new_base: the base to be put on front of all bases
        :param namespace: the namespace of the model
        :param properties: the properties declared in the model
        :param transformation_properties: the properties of the model
        """
        table_args = tuple(properties['add_in_table_args'])
        if table_args:
            new_base.define_table_args = self.define_table_args(
                new_base, namespace, table_args)
            transformation_properties['table_args'] = True

        if transformation_properties['table_kwargs'] is True:
            if sgdb_in(self.registry.engine, ['MySQL', 'MariaDB']):
                new_base.define_table_kwargs = self.define_table_kwargs(
                    new_base, namespace)

        self.insert_in_bases_table_args(new_base, transformation_properties)
        self.insert_in_bases_mapper_args(new_base, transformation_properties)

    def define_table_args(self, new_base, namespace, table_args):
        """
        :param new_base: the base to be put on front of all bases
        :param namespace: the namespace of the model
        """

        def fnct(cls_):
            if cls_.__registry_name__ == namespace:
                res = super(new_base, cls_).define_table_args()
                fks = [x.name for x in res
                       if isinstance(x, ForeignKeyConstraint)]

                t_args = []
                for field in table_args:
                    for constraint in field.update_table_args(self.registry,
                                                              cls_):
                        if (
                            not isinstance(constraint,
                                           ForeignKeyConstraint) or
                            constraint.name not in fks
                        ):
                            t_args.append(constraint)
                        elif isinstance(constraint, CheckConstraint):
                            t_args.append(constraint)  # pragma: no cover

                return res + tuple(t_args)

            return ()

        return classmethod(fnct)

    def define_table_kwargs(self, new_base, namespace):
        """
        :param new_base: the base to be put on front of all bases
        :param namespace: the namespace of the model
        """

        def fnct(cls_):
            res = {}
            if cls_.__registry_name__ == namespace:
                res = super(new_base, cls_).define_table_kwargs()

            res.update(dict(mysql_engine='InnoDB', mysql_charset='utf8'))
            return res

        return classmethod(fnct)

    def insert_in_bases_table_args(self, new_base, transformation_properties):
        """Add table __table_args__ in new_base

        :param new_base: the base to be put on front of all bases
        :param transformation_properties: the properties of the model
        """
        if (
            transformation_properties['table_args'] and
            transformation_properties['table_kwargs']
        ):

            def __table_args__(cls_):
                res = cls_.define_table_args() + (cls_.define_table_kwargs(),)
                return res

            new_base.__table_args__ = declared_attr(__table_args__)
        elif transformation_properties['table_args']:

            def __table_args__(cls_):
                return cls_.define_table_args()

            new_base.__table_args__ = declared_attr(__table_args__)
        elif transformation_properties['table_kwargs']:  # pragma: no cover

            def __table_args__(cls_):
                return cls_.define_table_kwargs()

            new_base.__table_args__ = declared_attr(__table_args__)

    def insert_in_bases_mapper_args(self, new_base, transformation_properties):
        """Add table __mapper_args__ in new_base

        :param new_base: the base to be put on front of all bases
        :param transformation_properties: the properties of the model
        """
        if transformation_properties['mapper_args']:

            def __mapper_args__(cls_):
                return cls_.define_mapper_args()

            new_base.__mapper_args__ = declared_attr(__mapper_args__)
