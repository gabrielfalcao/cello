#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict
MEMORY = defaultdict(list)


class Case(object):
    def __init__(self, stage):
        self.stage = stage

    def save(self, data):
        pass


class MemoryCase(Case):
    def save(self, data):
        MEMORY[self.stage.url].append(data)
