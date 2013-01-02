#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Case(object):
    '''
    Case is how stages are serialized upon calling `persist()`

    Example:

    MEMORY = defaultdict(list)

    class MemoryCase(Case):
        def save(self, data):
            MEMORY[self.stage.url].append(data)
    '''
    def __init__(self, stage):
        self.stage = stage

    def save(self, data):
        raise NotImplementedError(
            'you have to inherit cello.storage.Case '
            'and override the save method')


class DummyCase(Case):
    def save(self, data):
        pass
