from zope.interface import Interface
from anyblok import AnyBlok


@AnyBlok.target_registry(AnyBlok.Interface)
class ISqlAlchemyDataBase(Interface):
    """ Interface use to define database adapteur """

    def createdb(db):
        """Implement the create db for this proxy"""

    def dropdb(db):
        """ Implement the drop db for this proxy """

    def listdb():
        """ Implement the list dbs for this proxy """
