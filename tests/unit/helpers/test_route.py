#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from cello.helpers import Route, InvalidURLMapping
from sure import expect


def test_translating_route():
    "Route.translate will match the regex groups in the url mapping"

    class MyRoute(Route):
        url_mapping = 'this is a cool mapping: {name}'
        url_regex = re.compile(r'/(?P<name>\w+)$')

    expect(MyRoute.translate('http://yipit.com/admin')).to.equal(
        'this is a cool mapping: admin')


def test_translating_route_when_not_found():
    "Route.translate will match the regex groups in the url mapping"

    class MyRoute(Route):
        url_mapping = 'this is a cool mapping: {name}'
        url_regex = re.compile(r'/(?P<name>\w+)$')

    expect(MyRoute.translate).when.called_with('http://yipit.com/').to.throw(
        InvalidURLMapping,
        'url http://yipit.com/ does not match pattern /(?P<name>\w+)$')
