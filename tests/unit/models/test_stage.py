#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from mock import Mock
from mock import call
from mock import patch
from sure import expect
from cello.models import Stage
from cello.models import InvalidStateError
from cello.models import DOMWrapper
from cello.storage import Case
from cello.helpers import Route
from cello.helpers import InvalidURLMapping


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
    browser.get.return_value.url = 'http://foobar.com'

    FirstStage.visit(browser)

    browser.get.assert_called_once_with(
        'http://foobar.com',
        config=dict(screenshot=True),
    )


@patch('cello.models.lhtml')
def test_dom_is_a_dom_wrapper(lhtml):
    "Stage.dom returns a DOMWrapper is there is a valid response"
    stage = Stage(Mock(), response=Mock())

    expect(stage.dom).to.be.a(DOMWrapper)


def test_dom_raises_exception_if_response_is_none():
    "Stage.dom raises exception is self.response is None"

    class BoomStage(Stage):
        pass

    stage = BoomStage(Mock())

    def get_dom():
        return stage.dom

    expect(get_dom).when.called.to.throw(
        InvalidStateError,
        "The stage BoomStage hasn't been fetched yet, "
        "and so its DOM can't be queryed"
    )


def test_url_raises_if_no_parent():
    ("Stage.url will raise exception if router "
     "fails and it has no parent to fall back to")

    class MyCase(Case):
        def save(self, data):
            pass

    class MyRoute(Route):
        url_mapping = 'http://foo.bar.com/{page}'
        url_regex = re.compile(r'(?P<page>\w+).php')

    class SomeStage(Stage):
        route = MyRoute
        case = MyCase

    browser = Mock()
    st = SomeStage(browser=browser, url='http://foobar.com')

    def get_url():
        return st.url

    expect(get_url).when.called.to.throw(
        InvalidURLMapping,
        "url http://foobar.com does not match pattern (?P<page>\w+).php"
    )


def test_stage_with_next_stage():
    "Calling .visit() on a stage with next stage will persist the last stage"

    browser = Mock()
    r1 = Mock(url='http://request.one', html='<html><ul></ul></html>')
    r2 = Mock(url='http://request.two/product.php?id=123', html='<html><ul></ul></html>')

    browser.get.side_effect = [r1, r2]

    class TestCase(Case):
        def save(self, data):
            expect(data).to.equal({
                'url': 'http://weewoo.com/product.php?id=123',
                'response_url': 'http://request.two/product.php?id=123',
                'whatever': 123,
            })

    class LastStage(Stage):
        case = TestCase

        def play(self):
            self.scrape(['/product.php?id=123'])

        def tune(self):
            return {
                'whatever': 123,
                'response_url': self.response.url,

            }

    class FirstStage(Stage):
        url = 'http://weewoo.com'
        next_stage = LastStage

    FirstStage.visit(browser)

    browser.get.assert_has_calls([
        call('http://weewoo.com',
            config=dict(screenshot=True)),
        call('http://weewoo.com/product.php?id=123',
             config=dict(screenshot=True)),
    ])
