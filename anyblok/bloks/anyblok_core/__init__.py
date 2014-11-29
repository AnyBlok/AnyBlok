from anyblok.blok import Blok


class AnyBlokCore(Blok):
    """
    This blok is required by all anyblok application. This blok define the main
    fonctionnality to install, update and uninstall blok. And also list the
    known models, fields, columns and relationships:

    * Core model
    * Field Type
        - Function
    * Column Types:
        - DateTime
        - Decimal
        - Float
        - Time
        - BigInteger
        - Boolean
        - Date
        - Integer
        - Interval
        - LargeBinary
        - SmallInteger
        - String
        - Text
        - uString
        - uText
        - Selection
        - Json
    * Relationship types
        - One2One
        - Many2One
        - One2Many
        - Many2Many
    * System Models
        - Blok
        - Model
        - Field
        - Column
        - Relationship
    """

    version = '0.0.1'
    autoinstall = True
    priority = 0
