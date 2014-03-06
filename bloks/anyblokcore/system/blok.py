# -*- coding: utf-8 -*-
from anyblok.blok import BlokManager
from AnyBlok import target_registry
from AnyBlok.Model import System
from AnyBlok.Column import String, Integer


@target_registry(System)
class Blok:

    name = String(label="Name", primary_key=True, nullable=False)
    state = String(label="State", default='uninstalled', nullable=False)
    order = Integer(label="Order of loading", default=-1, nullable=False)

    @classmethod
    def list_by_state(cls, *states):
        if not states:
            return None

        res = {state: [] for state in states}
        bloks = cls.query().filter(cls.state.in_(states)).order_by(cls.order)
        for blok in bloks.all():
            res[blok.state].append(blok.name)

        if len(states) == 1:
            return res[states[0]]
        return res

    @classmethod
    def update_list(cls):
        #Do not remove blok because 2 or More AnyBlok api may use the same
        #Database

        Association = cls.registry.System.Blok.Association

        def populate_association(blok, links, mode, createifnotexist=False):
            for link in links:
                if createifnotexist:
                    if not cls.query().filter(cls.name == link).count():
                        cls.insert(name=link, state='undefined')
                query = Association.query()
                query = query.filter(Association.blok == blok)
                query = query.filter(Association.linked_blok == link)
                query = query.filter(Association.mode == mode)
                if not query.count():
                    Association.insert(blok=blok, linked_blok=link, mode=mode)

        #Create blok if not exist
        for order, blok in enumerate(BlokManager.ordered_bloks):
            b = cls.query().filter(cls.name == blok)
            if b.count():
                b.order = order
            else:
                cls.insert(name=blok, order=order)

        #Update required, optional, conditional
        for blok in BlokManager.ordered_bloks:
            entry = BlokManager.bloks[blok]

            populate_association(blok, entry.required, 'required')
            populate_association(blok, entry.optional, 'optional',
                                 createifnotexist=True)
            populate_association(blok, entry.conditional, 'conditional',
                                 createifnotexist=True)

    @classmethod
    def apply_state(cls, *bloks):
        Association = cls.registry.System.Blok.Association
        for blok in bloks:
            #Make the query in the loop to be sure to keep order
            b = cls.query().filter(cls.name == blok).first()
            entry = cls.registry.loaded_bloks[blok]
            if b.state in ('undefined', 'uninstalled', 'toinstall'):
                entry.install()
                b.state = 'installed'
            elif b.state == 'toupdate':
                entry.update()
                bloks = cls.query('name').filter(cls.state == 'installed')
                bloks = bloks.all()
                associate = Association.query()
                associate = associate.filter(Association.blok == blok)
                associate = associate.filter(associate.linked_blok.in_(bloks))
                associate.update(state='toupdate')
                b.state = 'installed'
            elif b.state == 'touninstall':
                entry.uninstall()
                bloks = cls.query('name')
                bloks = bloks.filter(cls.state in ('installed', 'toupdate'))
                bloks = bloks.all()
                associate = Association.query()
                associate = associate.filter(Association.blok == blok)
                associate = associate.filter(associate.linked_blok.in_(bloks))
                associate = associate.filter(associate.mode == 'required')
                associate.update(state='touninstall')
                b.state = 'uninstalled'


@target_registry(System.Blok)
class Association:

    blok = String(label="Blok", foreign_key=(System.Blok, 'name'),
                  nullable=False, primary_key=True)
    linked_blok = String(label="Linked blok",
                         foreign_key=(System.Blok, 'name'),
                         nullable=False, primary_key=True)
    mode = String(label="Mode of linked", nullable=False, primary_key=True)
