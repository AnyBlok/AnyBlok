# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy import CheckConstraint, ForeignKeyConstraint
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.ext.declarative import declared_attr

from ..common import sgdb_in
from .exceptions import ModelException
from .plugins import ModelPluginBase


def call_define_table_args(cls):
    return cls.define_table_args()


def call_define_table_kwargs(cls):
    return cls.define_table_kwargs()


def table_args_and_kwargs(cls):
    try:
        res = cls.call_define_table_args() + (cls.call_define_table_kwargs(),)
    except NoInspectionAvailable:  # pragma: no cover
        raise ModelException(
            "A Index  or constraint on the model "
            f'"{cls.__registry_name__}" if defined with SQLAlchemy'
            "class use the anyblok Index or constraint"
        )

    return res


def table_args(cls):
    return cls.call_define_table_args()


def table_kwargs(cls_):
    return cls_.call_define_table_kwargs()


def mapper_args(cls):
    res = cls.define_mapper_args()
    if "polymorphic_on" in res and res["polymorphic_on"]:
        column = res["polymorphic_on"]
        res["polymorphic_on"] = column.descriptor.sqla_column

    return res


class TableMapperPlugin(ModelPluginBase):
    def initialisation_tranformation_properties(
        self, properties, transformation_properties
    ):
        """Initialise the transform properties: hybrid_method

        :param new_type_properties: param to add in a new base if need
        """
        properties["add_in_table_args"] = []
        properties["call_define_table_args"] = classmethod(
            call_define_table_args
        )
        properties["call_define_table_kwargs"] = classmethod(
            call_define_table_kwargs
        )

        if "table_args" not in transformation_properties:
            transformation_properties["table_args"] = False
            transformation_properties["table_kwargs"] = False

        if "mapper_args" not in transformation_properties:
            transformation_properties["mapper_args"] = False

    def transform_base(self, namespace, base, transformation_properties):
        """Test if define_table/mapper_args are in the base, and call them
        save the value in the properties

        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param transformation_properties: the properties of the model
        """

        if hasattr(base, "define_table_args"):
            transformation_properties["table_args"] = True

        if hasattr(base, "define_table_kwargs"):
            transformation_properties["table_kwargs"] = True

        if hasattr(base, "define_mapper_args"):
            transformation_properties["mapper_args"] = True

    def before_model_construction(
        self, namespace, first_step, properties, transformation_properties
    ):
        table_args = tuple(properties["add_in_table_args"])
        if table_args:
            properties["call_define_table_args"] = self.define_table_args(
                namespace, table_args
            )
            transformation_properties["table_args"] = True

        if transformation_properties["table_kwargs"] is True:
            if sgdb_in(self.registry.engine, ["MySQL", "MariaDB"]):
                properties[
                    "call_define_table_kwargs"
                ] = self.define_table_kwargs(namespace)

        self.insert_table_args(properties, transformation_properties)
        self.insert_mapper_args(properties, transformation_properties)

    def define_table_args(self, namespace, table_args):
        """
        :param new_base: the base to be put on front of all bases
        :param namespace: the namespace of the model
        """

        def fnct(cls_):
            if cls_.__registry_name__ == namespace:
                res = cls_.define_table_args()
                fks = [
                    x.name for x in res if isinstance(x, ForeignKeyConstraint)
                ]

                t_args = []
                for field in table_args:
                    for constraint in field.update_table_args(
                        self.registry, cls_
                    ):
                        if (
                            not isinstance(constraint, ForeignKeyConstraint)
                            or constraint.name not in fks
                        ):
                            t_args.append(constraint)
                        elif isinstance(constraint, CheckConstraint):
                            t_args.append(constraint)  # pragma: no cover

                return res + tuple(t_args)

            return ()

        return classmethod(fnct)

    def define_table_kwargs(self, namespace):
        """
        :param new_base: the base to be put on front of all bases
        :param namespace: the namespace of the model
        """

        def fnct(cls_):
            res = {}
            if cls_.__registry_name__ == namespace:
                res = cls_.define_table_kwargs()

            res.update(dict(mysql_engine="InnoDB", mysql_charset="utf8"))
            return res

        return classmethod(fnct)

    def insert_table_args(self, properties, transformation_properties):
        if (
            transformation_properties["table_args"]
            and transformation_properties["table_kwargs"]
        ):
            properties["__table_args__"] = declared_attr(table_args_and_kwargs)
        elif transformation_properties["table_args"]:
            properties["__table_args__"] = declared_attr(table_args)
        elif transformation_properties["table_kwargs"]:  # pragma: no cover
            properties["__table_args__"] = declared_attr(table_kwargs)

    def insert_mapper_args(self, properties, transformation_properties):
        if transformation_properties["mapper_args"]:
            properties["__mapper_args__"] = declared_attr(mapper_args)
