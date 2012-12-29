#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urlparse import urlsplit
from functools import wraps
from lxml import html as lhtml

from .helpers import Route, InvalidURLMapping
from .storage import MemoryCase


stages = {}


def one_or_many(func):
    @wraps(func)
    def wrapper(*args, **kw):
        ret = func(*args, **kw)
        total = len(ret)
        if total == 1:
            return ret[-1]
        elif total > 1:
            return ret
        else:
            return None

    return wrapper


class DOMWrapper(object):
    def __init__(self, dom):
        self.dom = dom
        self.current_nodes = []

    def query(self, selector):
        self.current_nodes = self.dom.cssselect(selector)
        return self

    @one_or_many
    def attr(self, name):
        return map(lambda node: node.attrib.get(name, None),
                   self.current_nodes)

    @one_or_many
    def text(self):
        return map(lambda node: node.text.strip(),
                   self.current_nodes)

    @classmethod
    def from_response(cls, response):
        return cls(lhtml.fromstring(response.html))


class MetaStage(type):
    def __init__(cls, name, bases, attrs):
        if name not in ('MetaStage', 'Stage'):
            stages[name] = cls

        return super(MetaStage, cls).__init__(name, bases, attrs)


class Stage(object):
    __metaclass__ = MetaStage

    route = Route
    case = MemoryCase
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

        self.response = self.get_response(self.url)
        return self

    def get_response(self, url):
        return self.browser.get(
            self.url,
            config=dict(screenshot=True),
        )

    def next(self):
        response = self.get_response(self.url)
        stage = self.next_stage(self.browser, response=response, parent=self)
        stage.play()

    def scrape(self, links):
        for link in links:
            if self.next_stage:
                stage = self.next_stage(self.browser, url=link, parent=self).fetch()
                stage.play()

            else:
                stage = self.__class__(self.browser, url=link, parent=self).fetch()

            data = stage.tune()
            if not data:
                raise ValueError('Cannot persist without data')

            stage.persist(data)

    def play(self):
        self.fetch()

    def tune(self):
        return {}

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
        stage = Stage(browser, url=Stage.url)
        stage.next()
