#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import Mock
from sure import expect
from cello.models import Stage, InvalidStateError
from cello.storage import Case


def test_first_stage_requires_a_url():
    "The first stage always require an URL"
    browser = Mock()

    class FirstStage(Stage):
        pass

    expect(FirstStage.visit).when.called_with(browser).should.throw(
        InvalidStateError,
        "Trying to download content for FirstStage but it has no URL")


def test_stage_without_next_just_persist_as_is():
    "Calling .visit() on a stage with no next stage will persist it as is"
    browser = Mock()

    class TestCase(Case):
        def save(self, data):
            expect(data).to.equal({
                'url': 'http://foobar.com',
                'whatever': 123,
            })

    class FirstStage(Stage):
        url = 'http://foobar.com'
        case = TestCase

        def tune(self):
            return {
                'whatever': 123
            }

    browser.get.return_value.html = '<html><ul></ul></html>'

    FirstStage.visit(browser)

    browser.get.assert_called_once_with(
        'http://foobar.com',
        config=dict(screenshot=True),
    )
