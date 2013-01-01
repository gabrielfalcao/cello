#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import Mock, patch
from sure import expect
from cello.models import (
    DOMWrapper,
)


@patch('cello.models.lhtml')
def test_dom_wrapper_from_response(lhtml):
    "DOMWrapper.from_response creates a DOM from "

    response = Mock(html='<html></html>')
    wrapper = DOMWrapper.from_response(response)

    lhtml.fromstring.assert_called_once_with('<html></html>')
    expect(wrapper.dom).to.equal(lhtml.fromstring.return_value)


@patch('cello.models.Query')
def test_dom_wrapper_query_returns_query(Query):
    "DOMWrapper.query should return a Query object"

    Query.return_value.query.return_value = 'this result'

    dom = Mock()
    wrapper = DOMWrapper(dom)

    expect(wrapper.query('.menu a')).to.equal('this result')

    Query.assert_called_once_with(dom)
    Query.return_value.query.assert_called_once_with('.menu a')
