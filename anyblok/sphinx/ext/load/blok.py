# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.release import version
from anyblok.blok import BlokManager
from sphinx.ext.autodoc import ClassDocumenter, MethodDocumenter
from sphinx.util.docstrings import prepare_docstring


def default_autodoc_class(declaration):

    def wrapper(cls):
        return '\n\n'.join([
            ":Declaration type: %s" % declaration.__declaration_type__,
            ":Registry name: %s" % cls.__registry_name__])

    return wrapper


def default_autodoc_method(declaration):

    def wrapper(cls, meth_name, meth):
        return None

    return wrapper


class AnyBlokDeclarationDocumenter(ClassDocumenter):
    objtype = 'anyblok-declaration'
    directivetype = 'class'

    def get_doc(self, encoding=None, ignore=1):
        lines = getattr(self, '_new_docstrings', None)
        if lines is not None:
            return lines

        doc = super(AnyBlokDeclarationDocumenter, self).get_doc(
            encoding=encoding, ignore=ignore)

        registry_name = self.get_attr(self.object, '__registry_name__', None)
        declaration = self.get_attr(self.object, '__declaration__', None)
        if registry_name and declaration:
            autodoc = self.get_attr(declaration, 'autodoc_class',
                                    default_autodoc_class(declaration))
            docstrings = autodoc(self.object)
            if docstrings:
                doc.append(prepare_docstring(docstrings, ignore))

        return doc


class AnyBlokMethodDocumenter(MethodDocumenter):

    def get_doc(self, encoding=None, ignore=1):
        lines = getattr(self, '_new_docstrings', None)
        if lines is not None:
            return lines

        doc = super(AnyBlokMethodDocumenter, self).get_doc(encoding=encoding,
                                                           ignore=ignore)
        autodocs = self.get_attr(self.object, 'autodocs', [])
        for autodoc in autodocs:
            doc.append(prepare_docstring(autodoc, ignore))

        return doc


def setup(app):
    BlokManager.load()
    app.add_autodocumenter(AnyBlokDeclarationDocumenter)
    app.add_autodocumenter(AnyBlokMethodDocumenter)
    return {'version': version, 'parallel_read_safe': True}
