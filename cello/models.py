#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from urlparse import urlsplit
from lxml import html as lhtml

from .helpers import Route, InvalidURLMapping
from .storage import DummyCase

logger = logging.getLogger('cello')
logger.setLevel(logging.INFO)

DEBUG = True


class InvalidStateURLError(Exception):
    pass


class InvalidStateError(Exception):
    pass


class BadTuneReturnValue(Exception):
    msg = ('Could not persist while scraping the url "{url}" '
           'through {name} because the tune() method returned '
           'an empty value: {value}')


class CelloStopScraping(StopIteration):
    pass


class CelloJumpToNextStage(Exception):
    pass


class Query(str):
    def __init__(self, dom):
        self._dom = dom
        self._elements = []
        self._values = []
        self._last_query = "[Nothing queried so far]"

    def __repr__(self):
        total = len(self._elements)
        word = total == 1 and "element" or "elements"
        return u'<Query: "{}" with {} {}>'.format(self._last_query, total, word)

    def query(self, selector):
        selector = unicode(selector)
        self._last_query = selector
        self._elements = self._dom.cssselect(selector)
        return self

    def attr(self, name=None):
        func = lambda i: name and i.attrib.get(name, self) or dict(i.attrib)
        self._values = map(func, self._elements)
        return self

    def text(self):
        return self._one_or_many(map(lambda i: i.text and i.text.strip() or '',
                                     self._elements) or '')

    def html(self):
        return self._one_or_many(map(lhtml.tostring,
                                     self._elements) or '')

    def raw(self):
        ret = self._values or self._elements
        return self._one_or_many(ret)

    def one(self, index=0):
        raw = self.raw()
        if isinstance(raw, list):
            if len(raw) == 0:
                return ''
            else:
                return raw[index]
        else:
            return raw

    def first(self):
        return self.one(0)

    def last(self):
        return self.one(-1)

    def _one_or_many(self, ret):
        return len(ret) is 1 and ret[-1] or ret


class DOMWrapper(object):
    def __init__(self, dom):
        self.dom = dom
        self._query = Query(dom)

    def query(self, selector):
        return self._query.query(selector)

    @classmethod
    def from_response(cls, response):
        return cls(lhtml.fromstring(response.html))


class Stage(object):
    route = Route
    case = DummyCase
    next_stage = None

    def __init__(self, browser, url=None, response=None, parent=None):
        self.browser = browser
        self._url = url
        self.response = response
        self.parent = parent
        self.name = '.'.join([self.__class__.__module__, self.__class__.__name__])
        self.debug = DEBUG

    @property
    def dom(self):
        if self.response is None:
            raise InvalidStateError(
                "The stage %s hasn't been fetched yet, "
                "and so its DOM can't be queryed" % self.name
            )

        return DOMWrapper.from_response(self.response)

    @property
    def url(self):
        splitted = urlsplit(self._url)
        if splitted.scheme in ('http', 'https'):
            return self._url

        try:
            url = self.route.translate(self._url)
        except InvalidURLMapping:
            if not self.parent:
                raise

            return self.get_fallback_url()

        else:
            if not (url.startswith('http://') or url.startswith('https://')):
                return self.get_fallback_url()
            else:
                return url

    def absolute_url(self, path):
        result = urlsplit(self.url)
        return '{}://{}{}'.format(result.scheme, result.netloc, path)

    def get_fallback_url(self):
        if not self.parent:
            raise InvalidURLMapping(
                ('The stage %s has no parent to grab a base '
                'url from to add to %s') % (self.name, self._url))

        result = urlsplit(self.parent.url)
        return '{}://{}{}'.format(result.scheme, result.netloc, self._url)

    def fetch(self):
        if not self._url:
            raise ValueError('Try to call {}.fetch with no url'.format(self.name))

        self.response = self.get_response(self.url)

        return self

    def get_response(self, url):
        return self.browser.get(
            self.url,
            config=dict(screenshot=self.debug),
        )

    def proceed_to_next(self, link, using_response=None):
        if self.next_stage:
            stage = self.next_stage(self.browser, url=link, parent=self, response=using_response)
            stage.fetch()
            try:
                stage.play()
            except CelloJumpToNextStage:
                logger.warning("Jumping to next stage %s when calling .play() for url %s", repr(stage), link)
                return stage

        else:
            stage = self.__class__(self.browser, url=link, parent=self.parent, response=using_response)
            stage.fetch()
            stage.play()

        return stage

    def scrape(self, links, using_response=None):
        if isinstance(links, basestring):
            links = [links]

        for link in links:

            stage = self.proceed_to_next(link, using_response=using_response)

            try:
                data = stage.tune()
            except CelloJumpToNextStage:
                logger.warning("Jumping to next stage %s when calling .tune() for url %s", stage.name, link)
                continue

            if not data:
                raise BadTuneReturnValue(
                    BadTuneReturnValue.msg.format(
                        name=self.name,
                        url=stage.url,
                        value=repr(data),
                    )
                )

            stage.persist(data)

    def play(self):
        self.fetch()

    def tune(self):
        return {
            'datetime': datetime.now().isoformat(),
            'stage': self.name,
        }

    def persist(self, data):
        final = {
            'url': self.url,
        }
        payload = data or {}
        final.update(payload)

        storage = self.case(self)
        return storage.save(final)

    @classmethod
    def _start(Stage, browser):
        name = Stage.__name__

        if not isinstance(Stage.url, basestring):
            raise InvalidStateError(
                'Trying to download content for %s but it has no URL' % name)

        stage = Stage(browser, Stage.url)
        stage.proceed_to_next(Stage.url)
        data = stage.tune()
        stage.persist(data)

    @classmethod
    def visit(Stage, browser):
        try:
            return Stage._start(browser)
        except CelloStopScraping as e:
            return e
