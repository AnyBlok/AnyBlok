import anyblok
from anyblok._logging import log
from anyblok._argsparse import ArgsParseManager
from sqlalchemy import create_engine
from contextlib import contextmanager


class SqlAlchemyPostgres:
    """ Postgres adapter for database management"""

    __interface__ = 'postgres'

    @contextmanager
    def cnx(self):
        """ Context manager to get a connection to database """
        cnx = None
        try:
            postgres = ArgsParseManager.get_url(dbname='postgres')
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

    @log(withargs=True)
    def createdb(self, dbname):
        """ Create a database

        :param dbname: database name to create
        """
        with self.cnx() as conn:
            conn.execute("""create database "%s";""" % dbname)

    @log(withargs=True)
    def dropdb(self, dbname):
        """ Drop a database

        :param dbname: database name to drop
        """
        with self.cnx() as conn:
            conn.execute("""drop database "%s";""" % dbname)

    def listdb(self):
        """ list database

        :rtype: list of database name
        """
        select_clause = "select pg_db.datname"
        from_clause = " from pg_database pg_db"
        where_clause = " where pg_db.datname not in (%s)"
        values = ', '.join(["'template0'", "'template1'", "'postgres'"])

        username = ArgsParseManager.get('dbusername')
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
