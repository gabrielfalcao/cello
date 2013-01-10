#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cello.models import Stage
from cello.storage import Case, DummyCase
from sure import expect


def test_case_save_has_access_to_stage():
    "Case.save has access to stage"

    class MyStage(Stage):
        url = 'http://github.com'

    class MyCase(Case):
        def save(self, data):
            expect(self).to.have.property('stage').being.a(Stage)
            return 'bar'

    stage = MyStage(None)
    case = MyCase(stage)

    expect(case.save('foo')).to.equal('bar')


def test_it_requires_an_implementation():
    "A Case class must be implemented in order to work appropriately"

    expect(Case(None).save).when.called_with('data').to.throw(
        NotImplementedError,
        'you have to inherit cello.storage.Case '
        'and override the save method')


def test_dummy_case_doesnt_do_anything():
    "The DummyCase by default doesnt do anything"

    class MyStage(Stage):
        url = 'http://github.com'

    stage = MyStage(None)
    case = DummyCase(stage)

    expect(case.save('foo')).to.be.none
