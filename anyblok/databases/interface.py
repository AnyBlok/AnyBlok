from zope.interface import Interface


class ISqlAlchemyDataBaseType(Interface):
    """ Interface use to define database adapter

    The methods are:
        * createdb
        * dropdb
        * listdb
    """

    def createdb(db):
        """Implement the create db for this proxy"""

    def dropdb(db):
        """ Implement the drop db for this proxy """

    def listdb():
        """ Implement the list dbs for this proxy """
