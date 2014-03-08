# -*- coding: utf-8 -*-
#from alembic.migration import MigrationContext
#from alembic.autogenerate import compare_metadata
#from alembic.operations import Operations
#from sqlalchemy import schema
#        opts = {
#            'compare_type': True,
#            'compare_server_default': True,
#        }
#        mc = MigrationContext.configure(self.engine.connect(), opts=opts)
#        diff = compare_metadata(mc, self.declarativebase.metadata)
#
#        op = Operations(mc)
#
#        for d in diff:
#            if d[0] == 'add_column':
#                op.impl.add_column(d[2], d[3])
#                t = self.declarativebase.metadata.tables[d[2]]
#                for constraint in t.constraints:
#                    if not isinstance(constraint, schema.PrimaryKeyConstraint):
#                        op.impl.add_constraint(constraint)
#            elif isinstance(d[0], tuple):
#                for x in d:
#                    if x[0] == 'modify_type':
#                        op.alter_column(x[2], x[3], type_=x[6],
#                                        existing_type=x[5], **x[4])
#                    elif x[0] == 'modify_nullable':
#                        op.alter_column(x[2], x[3], nullable=x[6],
#                                        existing_nullable=x[5], **x[4])
#                    else:
#                        print(x)
#
#            else:
#                print(d)
#


class MigrationReport():

    def log_has(self, log):
        return False


class Migration:

    def __init__(self, engine, metadata):
        pass

    def add_column(self, tablename, column):
        pass

    def remove_column(self, tablename, columnname):
        pass

    def auto_upgrade_database(self):
        pass

    def detect_changed(self):
        report = MigrationReport()

        return report
