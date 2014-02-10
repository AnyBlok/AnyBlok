import anyblok
from zope.interface import implementer
from zope.component import getGlobalSiteManager
gsm = getGlobalSiteManager()
from sqlalchemy import create_engine
from contextlib import contextmanager


@implementer(anyblok.AnyBlok.Interface.ISqlAlchemyDataBase)
class SqlAlchemyPostgres(object):

    @contextmanager
    def cnx(self):
        cnx = None
        try:
            postgres = anyblok.ArgsParseManager.get_url(dbname='postgres')
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

    def createdb(self, dbname):
        with self.cnx() as conn:
            conn.execute("""create database "%s";""" % dbname)

    def dropdb(self, dbname):
        with self.cnx() as conn:
            conn.execute("""drop database "%s";""" % dbname)

    def listdb(self):
        select_clause = "select pg_db.datname"
        from_clause = " from pg_database pg_db"
        where_clause = " where pg_db.datname not in (%s)"
        values = ', '.join(["'template0'", "'template1'", "'postgres'"])

        username = anyblok.BlokManager.get('dbusername')
        if username:
            from_clause += ", pg_user pg_u"
            where_clause += " and pg_u.username = %s"
            values = [values, username]
            where_clause += " and pg_db.datdba=pg_u.usesysid"

        query = (select_clause + from_clause + where_clause) % values
        with self.cnx() as conn:
            res = conn.execute(query)

        return [x[0] for x in res.fetchall()]


postgres = SqlAlchemyPostgres()
gsm.registerUtility(
    postgres, anyblok.AnyBlok.Interface.ISqlAlchemyDataBase, 'postgres')
