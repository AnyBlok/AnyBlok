# -*- coding: utf-8 -*-
from anyblok import AnyBlok


class RegistryManager:
    """
    """

    loaded_bloks = {}
    declared_entries = []
    mustbeload_declared_entries = []

    @classmethod
    def declare_entry(cls, entry, mustbeload=False):
        """ Add new entry in the declared entry """
        if entry not in cls.declared_entries:
            cls.declared_entries.append(entry)

        if mustbeload:
            if entry not in cls.mustbeload_declared_entries:
                cls.mustbeload_declared_entries.append(entry)

    @classmethod
    def init_blok(cls, blokname):
        """ init one blok to be know by RegistryManager

        All bloks loaded must be initialize because the registry will be create
        with this information
        """
        blok = {
            'Core': {
                'Base': [],
                'SqlBase': [],
                'Session': [],
            }
        }
        for de in cls.declared_entries:
            blok[de] = {}

        cls.loaded_bloks[blokname] = blok

    @classmethod
    def has_core_in_target_registry(cls, blok, core):
        """ Return True if One Class exist in this blok for this core """
        return len(cls.loaded_bloks[blok]['Core'][core]) > 0

    @classmethod
    def add_core_in_target_registry(cls, core, cls_):
        """ Load core in blok

        warning the global var AnyBlok.current_blok must be field on the
        good blok
        core: is the existing core
        cls_: Class of the Core to save in loaded blok target registry
        """
        cls.loaded_bloks[AnyBlok.current_blok]['Core'][core].append(cls_)

    @classmethod
    def remove_core_in_target_registry(cls, blok, core, cls_):
        """ Remove Class in blok and in core """
        cls.loaded_bloks[blok]['Core'][core].remove(cls_)
