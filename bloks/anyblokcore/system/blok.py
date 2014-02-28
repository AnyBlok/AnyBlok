# -*- coding: utf-8 -*-
from anyblok.blok import BlokManager
from AnyBlok import target_registry
from AnyBlok.Model import System
from AnyBlok.Column import String  # , Enum


@target_registry(System)
class Blok:

    name = String(label="Name", primary_key=True)
    #state = Enum('Uninstall', 'To install', 'To update', 'To remove',
    #             'Installed', label="State of the blok", native_enum=String)

    @classmethod
    def list_by_state(cls, *states):
        #TODO
        return []

    @classmethod
    def update_list(cls):
        query = cls.query('name')
        query = query.filter(cls.name not in BlokManager.ordered_bloks)
        query.delete()

        for blok in BlokManager.ordered_bloks:
            if not cls.query().filter(cls.name == blok).count():
                cls.insert(name=blok)

    @classmethod
    def apply_state(cls, *bloks):
        #TODO
        pass
