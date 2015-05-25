import anyblok
from ..logging import log
from anyblok.config import Configuration
from sqlalchemy import create_engine
from contextlib import contextmanager
from logging import getLogger
logger = getLogger(__name__)


class SqlAlchemyPostgres:
    """ Postgres adapter for database management"""

    __interface__ = 'postgres'

    @contextmanager
    def cnx(self):
        """ Context manager to get a connection to database """
        cnx = None
        try:
            postgres = Configuration.get_url(db_name='postgres')
            engine = create_engine(postgres)
            cnx = engine.connect()
            cnx.execute("commit")
            yield cnx
            cnx.execute("commit")
        except Exception:
            if cnx:
                cnx.execute("rollback")
            raise
        finally:
            if cnx:
                cnx.close()

    @log(logger, withargs=True)
    def createdb(self, db_name):
        """ Create a database

        :param db_name: database name to create
        """
        with self.cnx() as conn:
            conn.execute("""create database "%s";""" % db_name)

    @log(logger, withargs=True)
    def dropdb(self, db_name):
        """ Drop a database

        :param db_name: database name to drop
        """
        with self.cnx() as conn:
            conn.execute("""drop database "%s";""" % db_name)

    def listdb(self):
        """ list database

        :rtype: list of database name
        """
        select_clause = "select pg_db.datname"
        from_clause = " from pg_database pg_db"
        where_clause = " where pg_db.datname not in (%s)"
        values = ', '.join(["'template0'", "'template1'", "'postgres'"])

        username = Configuration.get('db_user_name')
        if username:
            from_clause += ", pg_user pg_u"
            where_clause += " and pg_u.username = %s"
            values = [values, username]
            where_clause += " and pg_db.datdba=pg_u.usesysid"

        query = (select_clause + from_clause + where_clause) % values
        with self.cnx() as conn:
            res = conn.execute(query)

        return [x[0] for x in res.fetchall()]


anyblok.BDD['postgres'] = SqlAlchemyPostgres()
