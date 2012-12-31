#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cello import Case, Stage
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
