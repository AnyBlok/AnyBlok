from anyblok import Declarations
from anyblok.environment import EnvironmentManager
from logging import getLogger
logger = getLogger(__name__)


@Declarations.target_registry(Declarations.Exception)
class FieldException(Exception):
    """ Simple Exception for Field Adapter """


@Declarations.add_declaration_type()
class Field:
    """ Field class

    This class can't be instancied
    """

    @classmethod
    def target_registry(self, parent, name, cls_, **kwargs):
        """ add new sub registry in the registry and add it in the
        sys.modules

        :param parent: Existing in the declaration
        :param name: Name of the new field to add it
        :param cls_: Class Interface to add
        """
        _registryname = parent.__registry_name__ + '.' + name
        if hasattr(parent, name) and not EnvironmentManager.get('reload',
                                                                False):
            raise FieldException("The Field %r already exist" % _registryname)

        setattr(parent, name, cls_)
        logger.info("Add new type field : %r" % _registryname)

    @classmethod
    def remove_registry(self, registry, child, cls_, **kwargs):
        """ Forbidden method """
        raise FieldException("Remove a field is forbiden")

    def __init__(self, label=None):
        """ Initialise the field

        :param label: label of this field
        :type label: str
        """
        self.MustNotBeInstanced(Field)
        if label is None:
            raise FieldException("Label argument are required")
        self.label = label

    def MustNotBeInstanced(self, cls):
        """ Raise an exception if the cls is an instance of this __class__

        :param cls: instance of the class
        """
        if self.__class__ is cls:
            raise FieldException(
                "%r class must not be instanced use a sub class" % cls)

    def update_properties(self, registry, namespace, fieldname, properties):
        """ Update the propertie use to add new column

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        """

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        :rtype: instance of Field
        """
        return self

    def native_type(cls):
        """ Return the native SqlAlchemy type """
        raise FieldException("No native type for this field")
