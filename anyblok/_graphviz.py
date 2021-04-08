# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from graphviz.dot import Digraph


class BaseSchema:
    """Common class extended by the type of schema"""

    def __init__(self, name, format='png'):
        self.name = name
        self.format = format
        self._nodes = {}
        self._edges = {}
        self.count = 0

    def add_edge(self, cls_1, cls_2, attr=None):
        """Add a new edge between two nodes

        ::

            dot.add_edge(node1, node2)

        :param cls_1: node (string or object) - from
        :param cls_2: node (string or object) - to
        :param attr: attribute of the edge
        """
        cls_1 = cls_1 if isinstance(cls_1, str) else cls_1.name
        cls_2 = cls_2 if isinstance(cls_2, str) else cls_2.name
        self.count += 1
        self._edges["%s_%s_2_%d" % (cls_1, cls_2, self.count)] = {
            'from': cls_1,
            'to': cls_2,
            'attr': {} if attr is None else attr
        }

    def render(self):
        """Call graphviz to create the schema """
        self.dot = Digraph(name=self.name, format=self.format,
                           node_attr={'shape': 'record',
                                      'style': 'filled',
                                      'fillcolor': 'gray95'})
        for _, cls in self._nodes.items():
            cls.render(self.dot)

        for _, edge in self._edges.items():
            self.dot.edge(edge['from'], edge['to'],
                          _attributes=edge['attr'])

    def save(self):
        """Render and create the output file """
        self.render()
        self.dot.render(self.name)


class TableSchema:
    """Describe one table """

    def __init__(self, name, parent, islabel=False):
        self.name = name
        self.parent = parent
        self.islabel = islabel
        self.column = []

    def render(self, dot):
        """Call graphviz to create the schema """
        if self.islabel:
            label = "{%s}" % self.name
        else:
            column = '\\n'.join(self.column)
            label = "{%s|%s}" % (self.name, column)

        dot.node(self.name, label=label)

    def add_column(self, name, type_, primary_key=False):
        """Add a new column to the table

        :param name: the name of the column
        :param type_: the type of the column
        :param primary_key: if True, 'PK' argument will be added
        """
        self.column.append("%s%s (%s)" % (
            'PK ' if primary_key else '', name, type_))

    def add_foreign_key(self, node, label=None, nullable=True):
        """Add a new foreign key

        :param node: node (string or object) of the table attached
        :param label: name of the column to add the foreign key to
        TODO: i did not understand the explanation of 'nullable' parameter
        :param nullable: boolean to select the multiplicity of the association
        """
        self.parent.add_foreign_key(self, node, label, nullable)


class SQLSchema(BaseSchema):
    """Create a schema to display the table model

    ::

        dot = SQLSchema('the name of my schema')
        t1 = dot.add_table('Table 1')
        t1.add_column('c1', 'Integer')
        t1.add_column('c2', 'Integer')
        t2 = dot.add_table('Table 2')
        t2.add_column('c1', 'Integer')
        t2.add_foreign_key(t1, 'c2')
        dot.save()
    """

    def add_table(self, name):
        """Add a new node TableSchema with columns

        :param name: the name of the table
        :rtype: returns an instance of TableSchema
        """
        tmp = TableSchema(name, self)
        self._nodes[name] = tmp
        return tmp

    def add_label(self, name):
        """Add a new node TableSchema without column

        :param name: the name of the table
        :rtype: returns an instance of TableSchema
        """
        tmp = TableSchema(name, self, islabel=True)
        self._nodes[name] = tmp
        return tmp

    def get_table(self, name):
        """Return the instance of TableSchema linked to the table name given

        :param name: the name of the table
        :rtype: return an instance of TableSchema
        """
        return self._nodes.get(name)

    def add_foreign_key(self, cls_1, cls_2, label=None, nullable=False):
        multiplicity = "0..1" if nullable else "1"
        hlabel = '%s (%s)' % (label, multiplicity) if label else multiplicity

        self.add_edge(cls_1, cls_2, attr={
            'arrowhead': "none",
            'headlabel': hlabel,
        })


class ClassSchema:
    """Used to display a class """

    def __init__(self, name, parent, islabel=False):
        self.name = name
        self.parent = parent
        self.islabel = islabel
        self.properties = []
        self.column = []
        self.method = []

    def extend(self, node):
        """Add an edge with extended shape to the node

        :param node: node (string or object)
        """
        self.parent.add_extend(self, node)

    def strong_aggregate(self, node,
                         label_from=None, multiplicity_from=None,
                         label_to=None, multiplicity_to=None):
        """Add an edge with strong aggregate shape to the node

        :param node: node (string or object)
        :param label_from: the name of the attribute
        :param multiplicity_from: multiplicity of the attribute
        :param label_to: the name of the attribute
        :param multiplicity_to: multiplicity of the attribute
        """
        self.parent.add_strong_aggregation(self, node, label_from,
                                           multiplicity_from, label_to,
                                           multiplicity_to)

    def aggregate(self, node,
                  label_from=None, multiplicity_from=None,
                  label_to=None, multiplicity_to=None):
        """Add an edge with aggregate shape to the node

        :param node: node (string or object)
        :param label_from: the name of the attribute
        :param multiplicity_from: multiplicity of the attribute
        :param label_to: the name of the attribute
        :param multiplicity_to: multiplicity of the attribute
        """
        self.parent.add_aggregation(self, node, label_from, multiplicity_from,
                                    label_to, multiplicity_to)

    def associate(self, node,
                  label_from=None, multiplicity_from=None,
                  label_to=None, multiplicity_to=None):
        """Add an edge with associate shape to the node

        :param node: node (string or object)
        :param label_from: the name of the attribute
        :param multiplicity_from: multiplicity of the attribute
        :param label_to: the name of the attribute
        :param multiplicity_to: multiplicity of the attribute
        """
        self.parent.add_association(self, node, label_from, multiplicity_from,
                                    label_to, multiplicity_to)

    def add_property(self, name):
        """Add a property to the class

        :param name: the name of the property
        """
        self.properties.append(name)

    def add_column(self, name):
        """Add a column to the class

        :param name: the name of the column
        """
        self.column.append(name)

    def add_method(self, name):
        """Add a method to the class

        :param name: the name of the method
        """
        self.method.append(name)

    def render(self, dot):
        """Call graphviz to create the schema """
        if self.islabel:
            label = "{%s}" % self.name
        else:
            properties = '\\n'.join(self.properties)
            column = '\\n'.join(self.column)
            method = '\\n'.join('%s()' % x for x in self.method)
            label = "{%s|%s|%s|%s}" % (self.name, properties, column, method)

        dot.node(self.name, label=label)


class ModelSchema(BaseSchema):
    """Create a schema to display the UML model

    ::

        dot = ModelSchema('The name of my UML schema')
        cls = dot.add_class('My class')
        cls.add_method('insert')
        cls.add_property('items')
        cls.add_column('my column')
        dot.save()
    """

    def add_class(self, name):
        """Add a new node ClassSchema with column

        :param name: the name of the class
        :rtype: return an instance of ClassSchema
        """
        tmp = ClassSchema(name, self)
        self._nodes[name] = tmp
        return tmp

    def add_label(self, name):
        """Return an instance of ClassSchema linked to the class name given

        :param name: the name of the class
        :rtype: return an instance of ClassSchema
        """
        tmp = ClassSchema(name, self, islabel=True)
        self._nodes[name] = tmp
        return tmp

    def get_class(self, name):
        """Add a new node ClassSchema without column

        :param name: the name of the class
        :rtype: return an instance of ClassSchema
        """
        return self._nodes.get(name)

    def add_extend(self, cls_1, cls_2):
        """Add edge to extend

        :param cls_1: the name of the class 1
        :param cls_2: the name of the class 2
        """
        self.add_edge(cls_1, cls_2, attr={
            'dir': 'back',
            'arrowtail': 'empty',
        })

    def add_aggregation(self, cls_1, cls_2,
                        label_from=None, multiplicity_from=None,
                        label_to=None, multiplicity_to=None):
        """Add edge for aggregation

        :param cls_1: the name of the class 1
        :param cls_2: the name of the class 2
        :param label_from: attribute name
        :param multiplicity_from: multiplicity of the attribute
        :param label_to: attribute name
        :param multiplicity_to: multiplicity of the attribute
        :return:
        """
        label_from, label_to = self.format_label(
            label_from, multiplicity_from, label_to, multiplicity_to)

        if not cls_1 or not cls_2:
            return  # pragma: no cover

        self.add_edge(cls_1, cls_2, attr={
            'dir': 'back',
            'arrowtail': 'odiamond',
            'headlabel': label_from,
            'taillabel': label_to,
        })

    def add_strong_aggregation(self, cls_1, cls_2,
                               label_from=None, multiplicity_from=None,
                               label_to=None, multiplicity_to=None):
        """Add edge for strong aggregation

        :param cls_1:
        :param cls_2:
        :param label_from:
        :param multiplicity_from:
        :param label_to:
        :param multiplicity_to:
        :return:
        """
        label_from, label_to = self.format_label(
            label_from, multiplicity_from, label_to, multiplicity_to)
        self.add_edge(cls_1, cls_2, attr={
            'dir': 'back',
            'arrowtail': 'diamond',
            'headlabel': label_from,
            'taillabel': label_to,
        })

    @staticmethod
    def format_label(label_from, multiplicity_from, label_to,
                     multiplicity_to):
        def _format_label(label, multiplicity):
            if label:
                if multiplicity:
                    return '%s (%s)' % (label, multiplicity)

                return label
            else:
                if multiplicity:
                    return multiplicity

                return

        return (
            _format_label(label_from, multiplicity_from),
            _format_label(label_to, multiplicity_to),
        )

    def add_association(self, cls_1, cls_2,
                        label_from=None, multiplicity_from=None,
                        label_to=None, multiplicity_to=None):
        label_from, label_to = self.format_label(
            label_from, multiplicity_from, label_to, multiplicity_to)
        self.add_edge(cls_1, cls_2, attr={
            'arrowhead': "none",
            'headlabel': label_from,
            'taillabel': label_to,
        })
