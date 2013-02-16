#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from mock import Mock
from mock import call
from mock import patch
from sure import expect
from cello import models
from cello.models import Stage
from cello.models import InvalidStateError
from cello.models import DOMWrapper
from cello.models import CelloStopScraping
from cello.models import CelloJumpToNextStage
from cello.models import BadTuneReturnValue
from cello.storage import Case
from cello.helpers import Route
from cello.helpers import InvalidURLMapping

models.DEBUG = True


def test_first_stage_requires_a_url():
    "The first stage always require an URL"
    browser = Mock()

    class FirstStage(Stage):
        pass

    expect(FirstStage.visit).when.called_with(browser).should.throw(
        InvalidStateError,
        "Trying to download content for FirstStage but it has no URL")


def test_stop_scraping_all_of_the_sudden():
    "Calling .visit() handles CelloStopScraping"
    browser = Mock()

    class StoppableStage(Stage):
        url = 'http://foobar.com'

        def play(self):
            raise CelloStopScraping('LOL')

    browser.get.return_value.html = '<html><ul></ul></html>'
    browser.get.return_value.url = 'http://foobar.com'

    StoppableStage.visit(browser)


def test_absolute_url():
    "Calling .absolute_url(path) returns absolute url given relative path"

    class AbsoluteStage(Stage):
        url = 'http://foobar.com'

    st = AbsoluteStage(Mock())
    expect(st.absolute_url("/123")).to.equal('http://foobar.com/123')


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
        ("The stage tests.unit.models.test_stage.BoomStage hasn't been fetched yet, and so its DOM can't be queryed")
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
    st = SomeStage(browser=browser, url='sfoobar.com')

    def get_url():
        return st.url

    expect(get_url).when.called.to.throw(
        InvalidURLMapping,
        "url sfoobar.com does not match pattern (?P<page>\w+).php"
    )


def test_url_fallsback_to_parent_if_routed_is_not_absolute():
    ("Stage.url will get the base url from its parent "
     "if the routed url is not absolute")

    class MyRoute(Route):
        url_mapping = 'foo.bar.com/{page}'
        url_regex = re.compile(r'(?P<page>.*).php')

    class ChildrenSomeStage(Stage):
        route = MyRoute

    class SomeStage(Stage):
        url = 'http://awesome.io'
        next_stage = ChildrenSomeStage

    browser = Mock()
    parent = SomeStage(browser=browser)
    st = ChildrenSomeStage(browser=browser, parent=parent, url='/test/one.php')

    expect(st.url).to.equal('http://awesome.io/test/one.php')


def test_url_using_mapping():
    ("Stage.url will attempt to use the URL from the route")

    class MyRoute(Route):
        url_mapping = 'https://ginger.io/{page}'
        url_regex = re.compile(r'/(?P<page>.*).php')

    class ChildrenSomeStage(Stage):
        route = MyRoute

    class SomeStage(Stage):
        url = 'http://awesome.io'
        next_stage = ChildrenSomeStage

    browser = Mock()
    parent = SomeStage(browser=browser)
    st = ChildrenSomeStage(browser=browser, parent=parent, url='/zero/2.php')

    expect(st.url).to.equal('https://ginger.io/zero/2')


def test_url_fallsback_to_parent_if_router_fails():
    ("Stage.url will get the base url from its parent "
     "if the router fails")

    class MyRoute(Route):
        url_mapping = 'http://foo.bar.com/{page}'
        url_regex = re.compile(r'(?P<page>nothing hahaha).php')

    class ChildrenSomeStage(Stage):
        route = MyRoute

    class SomeStage(Stage):
        next_stage = ChildrenSomeStage

    browser = Mock()
    parent = SomeStage(browser=browser, url='http://foobar.com')
    st = ChildrenSomeStage(browser=browser, parent=parent, url='/test/one')

    expect(st.url).to.equal('http://foobar.com/test/one')


def test_get_fallback_url_raises_if_has_no_parent():
    ("Stage.get_fallback_url should raise InvalidURLMapping if there is no parent")

    class ChildStage(Stage):
        pass

    st = ChildStage(browser=Mock(), url='/test/child/')

    expect(st.get_fallback_url).when.called.to.throw(
        InvalidURLMapping, "The stage tests.unit.models.test_stage.ChildStage has no parent to grab a base url from to add to /test/child/")


def test_fetch_called_with_no_url():
    ("Stage.fetch should raise ValueError if the stage has no url")

    class SomeStage(Stage):
        pass

    st = SomeStage(browser=Mock())

    expect(st.fetch).when.called.to.throw(
        ValueError, "Try to call tests.unit.models.test_stage.SomeStage.fetch with no url")


@patch('cello.models.logger')
def test_proceed_to_next_logs_when_play_raises_error(logger):
    ("Stage.proceed_to_next logs a warning and returns stage directly when play throws CelloJumpToNextStage")

    class SecondStage(Stage):
        def play(self):
            raise CelloJumpToNextStage('next')

    class FirstStage(Stage):
        next_stage = SecondStage

    browser = Mock()

    st = FirstStage(browser)
    second_stage = st.proceed_to_next('http://foobar.com')

    logger.warning.assert_called_once_with(
        'Jumping to next stage %s when calling .play() for url %s',
        repr(second_stage),
        'http://foobar.com',
    )


def test_scrape_should_persist_data_in_the_end():
    ("Stage.scrape should persist the data after processing each link")

    persist_mock = Mock()

    class FirstStage(Stage):
        def tune(self):
            return {
                'foo': 'bar',
            }

        persist = persist_mock

    browser = Mock()

    st = FirstStage(browser)
    st.scrape(['http://google.com'])
    persist_mock.assert_called_once_with({'foo': 'bar'})


@patch('cello.models.logger')
def test_scrape_logs_when_tune_raises_error(logger):
    ("Stage.scrape logs a warning when tune throws CelloJumpToNextStage")

    class FirstStage(Stage):
        def tune(self):
            raise CelloJumpToNextStage('wow')

    browser = Mock()

    st = FirstStage(browser)
    st.scrape('http://google.com')

    logger.warning.assert_called_once_with(
        "Jumping to next stage %s when calling .tune() for url %s",
        'tests.unit.models.test_stage.FirstStage',
        'http://google.com',
    )


def test_scrape_raises_if_tune_returns_empty_results():
    ("Stage.scrape raises BadTuneReturnValue if tune returns a falsy value")

    class MessedUpTuneStage(Stage):
        def tune(self):
            return None

    browser = Mock()

    st = MessedUpTuneStage(browser)

    expect(st.scrape).when.called_with(['http://foobar.com']).to.throw(
        BadTuneReturnValue,
        ('Could not persist while scraping the url "http://foobar.com" '
         'through tests.unit.models.test_stage.MessedUpTuneStage because the tune() method returned '
         'an empty value: None')
    )


def test_play_calls_fetch_by_default():
    ("Stage.play() by default just calls fetch()")

    class PlayStage(Stage):
        fetch = Mock()

    st = PlayStage(Mock())
    st.play()

    PlayStage.fetch.assert_called_once_with()


@patch('cello.models.datetime')
def test_tune_calls_fetch_by_default(datetime):
    ("Stage.tune() by default returns datetime and stage name")

    datetime.now.return_value.isoformat.return_value = '[iso date]'

    class TuneStage(Stage):
        pass

    st = TuneStage(Mock())
    data = st.tune()

    expect(data).to.equal({
        'datetime': '[iso date]',
        'stage': 'tests.unit.models.test_stage.TuneStage',
    })
