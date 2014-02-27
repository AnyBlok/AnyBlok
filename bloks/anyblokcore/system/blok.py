# -*- coding: utf-8 -*-
#from anyblok.blok import BlokManager
from AnyBlok import target_registry
from AnyBlok.Model import System
from AnyBlok.Column import String


@target_registry(System)
class Blok:

    name = String(label="Name", primary_key=True)

    @classmethod
    def list_by_state(cls, *states):
        #TODO
        return []

    @classmethod
    def update_list(cls):
        #TODO
        pass

    @classmethod
    def apply_state(cls, *bloks):
        #TODO
        pass
