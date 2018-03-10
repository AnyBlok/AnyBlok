# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.release import version
from anyblok.blok import BlokManager
from anyblok.model import autodoc_fields
from sphinx.ext.autodoc import ClassDocumenter, MethodDocumenter
from sphinx.util.docstrings import prepare_docstring


def autodoc_registration(declaration, cls):
    res = ["**AnyBlok registration**:",
           "",
           "- Type: " + declaration.__declaration_type__,
           "- Registry name: " + cls.__registry_name__,
           ]
    if getattr(declaration, 'autodoc_anyblok_kwargs', False):
        res.extend('- %s: %s' % (x.replace('_', ' ').strip().capitalize(), y)
                   for x, y in cls.__anyblok_kwargs__.items()
                   if x != '__registry_name__')

    if getattr(declaration, 'autodoc_anyblok_bases', False):
        ab_bases = cls.__anyblok_bases__
        if ab_bases:
            res.extend(['- Inherited Models or Mixins:', ''])
            res.extend('  * :class:`%s.%s`' % (c.__module__, c.__name__)
                       for c in ab_bases)
            res.append('')
    res.extend(('', ''))
    return '\n'.join(res)


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
            autodoc = self.get_attr(declaration, 'autodoc_class', None)
            if autodoc is not None:
                docstrings = autodoc(self.object)
            else:
                docstrings = autodoc_registration(declaration, self.object)
                if getattr(declaration, 'autodoc_anyblok_fields', False):
                    docstrings += autodoc_fields(declaration, self.object)
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
