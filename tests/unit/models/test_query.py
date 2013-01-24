#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import Mock, patch
from sure import expect
from cello.models import Query


def test_query_methods_never_fail_by_returning_itself():
    "Query methods never fail because it always returns itself"

    dom = Mock()
    dom.cssselect.return_value = []
    query = Query(dom)

    expect(query.query('a')).to.be.a(Query)
    expect(query.query('a').attr('href')).to.be.a(Query)

# Testing .__repr__


def test_query_and_repr_with_no_objects():
    "Query by atributes with no objects"

    dom = Mock()

    dom.cssselect.return_value = range(10)

    query = Query(dom)

    expect(repr(query.query('li a'))).to.equal('<Query: "li a" with 10 elements>')


# Testing .attr

def test_query_and_attr_with_no_objects():
    "Query by atributes with no objects"

    dom = Mock()

    dom.cssselect.return_value = []

    query = Query(dom)

    q = query.query('li a').attr('href')
    expect(q).to.be.a(Query)
    expect(q.raw()).to.equal([])


def test_query_and_attr_with_many_objects():
    "Query by atributes with many"

    dom = Mock()
    l1 = Mock(attrib={'href': 'http://yipit.com'})
    l2 = Mock(attrib={'href': 'http://github.com'})

    dom.cssselect.return_value = [l1, l2]

    query = Query(dom)

    expect(query.query('li a').attr('href').raw()).to.equal([
        'http://yipit.com',
        'http://github.com',
    ])


def test_query_and_attr_with_one_object():
    "Query by atributes with one object"

    dom = Mock()
    link = Mock(attrib={'href': 'http://yipit.com'})

    dom.cssselect.return_value = [link]

    query = Query(dom)

    expect(query.query('li a').attr('href').raw()).to.equal(
        'http://yipit.com')


# .one ()

def test_query_attr_one_with_many_objects():
    "Query by atributes with many and calling .one()"

    dom = Mock()
    l1 = Mock(attrib={'href': 'http://yipit.com'})
    l2 = Mock(attrib={'href': 'http://github.com'})

    dom.cssselect.return_value = [l1, l2]

    query = Query(dom)

    expect(query.query('li a').attr('href').one()).to.equal(
        'http://yipit.com')


def test_query_attr_one_with_one_object():
    "Query by atributes with one object"

    dom = Mock()
    link = Mock(attrib={'href': 'http://yipit.com'})

    dom.cssselect.return_value = [link]

    query = Query(dom)

    expect(query.query('li a').attr('href').one()).to.equal(
        'http://yipit.com')


def test_query_attr_one_with_no_objects():
    "Query by atributes with no objects"

    dom = Mock()
    dom.cssselect.return_value = []

    query = Query(dom)

    expect(query.query('li a').attr('href').one()).to.equal('')


# Testing .first

def test_query_attr_first_with_many_objects():
    "Query by atributes with many and calling .first()"

    dom = Mock()
    l1 = Mock(attrib={'href': 'http://yipit.com'})
    l2 = Mock(attrib={'href': 'http://github.com'})

    dom.cssselect.return_value = [l1, l2]

    query = Query(dom)

    expect(query.query('li a').attr('href').first()).to.equal(
        'http://yipit.com')


def test_query_attr_first_with_first_object():
    "Query by atributes with one object"

    dom = Mock()
    link = Mock(attrib={'href': 'http://yipit.com'})

    dom.cssselect.return_value = [link]

    query = Query(dom)

    expect(query.query('li a').attr('href').first()).to.equal(
        'http://yipit.com')


def test_query_attr_first_with_no_objects():
    "Query by atributes with no objects"

    dom = Mock()
    dom.cssselect.return_value = []

    query = Query(dom)

    expect(query.query('li a').attr('href').first()).to.equal('')


# Testing .last

def test_query_attr_last_with_many_objects():
    "Query by atributes with many and calling .last()"

    dom = Mock()
    l1 = Mock(attrib={'href': 'http://yipit.com'})
    l2 = Mock(attrib={'href': 'http://github.com'})

    dom.cssselect.return_value = [l1, l2]

    query = Query(dom)

    expect(query.query('li a').attr('href').last()).to.equal(
        'http://github.com')


def test_query_attr_last_with_last_object():
    "Query by atributes with one object"

    dom = Mock()
    link = Mock(attrib={'href': 'http://yipit.com'})

    dom.cssselect.return_value = [link]

    query = Query(dom)

    expect(query.query('li a').attr('href').last()).to.equal(
        'http://yipit.com')


def test_query_attr_last_with_no_objects():
    "Query by atributes with no objects"

    dom = Mock()
    dom.cssselect.return_value = []

    query = Query(dom)

    expect(query.query('li a').attr('href').last()).to.equal('')


# Testing .text

def test_query_and_text_with_no_objects():
    "Query and retrieve text with no objects"

    dom = Mock()

    dom.cssselect.return_value = []

    query = Query(dom)
    expect(query.query('ul.menu li a').text()).to.equal('')


def test_query_and_text_with_many_objects():
    "Query and retrieve text with many objects"

    dom = Mock()
    l1 = Mock(text='  foo  ')
    l2 = Mock(text=' \n bar \n  ')

    dom.cssselect.return_value = [l1, l2]

    query = Query(dom)
    expect(query.query('ul.menu li a').text()).to.equal(['foo', 'bar'])


def test_query_and_text_with_one_object():
    "Query and retrieve text with one object"

    dom = Mock()
    l1 = Mock(text='  foo  ')

    dom.cssselect.return_value = [l1]

    query = Query(dom)
    expect(query.query('ul.menu li a').text()).to.equal('foo')


# Testing .html

@patch('cello.models.lhtml')
def test_query_and_html_calls_tostring(lhtml):
    "Query and retrieve html calls lxml"

    dom = Mock()

    lhtml.tostring.return_value = '<a></a>'
    dom.cssselect.return_value = ['whatever']

    query = Query(dom)
    expect(query.query('ul.menu li a').html()).to.equal('<a></a>')

    lhtml.tostring.assert_called_once_with('whatever')
