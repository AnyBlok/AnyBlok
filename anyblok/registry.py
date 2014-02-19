# -*- coding: utf-8 -*-


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
