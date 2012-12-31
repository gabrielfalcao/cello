#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
from urlparse import urlsplit
from lxml import html as lhtml

from .helpers import Route, InvalidURLMapping
from .storage import Case


class BadTuneReturnValue(Exception):
    pass


class Query(object):
    def __init__(self, dom):
        self._dom = dom
        self._elements = []
        self._values = []

    def query(self, selector):
        self._elements = self._dom.cssselect(selector)
        return self

    def attr(self, name):
        func = lambda i: i.attrib.get(name, self)
        self._values = map(func, self._elements)
        return self

    def text(self):
        return self._one_or_many(map(lambda i: i.text.strip(),
                                     self._elements) or '')

    def html(self):
        return lhtml.tostring(self._elements)

    def raw(self):
        ret = self._values or self._elements
        return self._one_or_many(ret)

    def _one_or_many(self, ret):
        return len(ret) is 1 and ret[-1] or ret


class DOMWrapper(object):
    def __init__(self, dom):
        self.dom = dom
        self.__query = Query(dom)

    def query(self, selector):
        return self.__query.query(selector)

    @classmethod
    def from_response(cls, response):
        return cls(lhtml.fromstring(response.html))


class Stage(object):
    route = Route
    case = Case
    next_stage = None

    def __init__(self, browser, url=None, response=None, parent=None):
        self.browser = browser
        self._url = url
        self.response = response
        self.parent = parent

    @property
    def dom(self):
        if self.response is None:
            return None

        return DOMWrapper.from_response(self.response)

    @property
    def url(self):
        try:
            return self.route.translate(self._url)
        except InvalidURLMapping:
            if not self.parent:
                raise
            result = urlsplit(self.parent.response.url)
            return '{}://{}{}'.format(result.scheme, result.netloc, self._url)

    def fetch(self):
        if not self._url:
            raise ValueError('Want me to fetch without a url')

        if not self.response:
            self.response = self.get_response(self.url)

        return self

    def get_response(self, url):
        return self.browser.get(
            self.url,
            config=dict(screenshot=True),
        )

    def proceed_to_next(self, link):
        if self.next_stage:
            stage = self.next_stage(self.browser, url=link, parent=self)
            stage.fetch()
            stage.play()
        else:
            stage = self.__class__(self.browser, url=link, parent=self)
            stage.fetch()

        return stage

    def scrape(self, links):
        for link in links:
            stage = self.proceed_to_next(link)
            data = stage.tune()

            if not data:
                raise BadTuneReturnValue('Cannot persist without data')

            stage.persist(data)

    def play(self):
        self.fetch()

    def tune(self):
        return {
            'datetime': datetime.now().isoformat(),
            'stage': self.__class__.__name__,
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
    def visit(Stage, browser):
        stage = Stage(browser)
        stage.proceed_to_next(Stage.url)
