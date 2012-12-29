#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sure import expect
from cello.models import one_or_many


def test_one_or_many_returning_one():
    "@one_or_many decorator returns one item if the list has only one item"

    @one_or_many
    def list_with_1_item():
        return ['the item']

    expect(list_with_1_item()).to.be.a(str)
    expect(list_with_1_item()).to.equal('the item')


def test_one_or_many_returning_many():
    "@one_or_many decorator returns a list of items if has more than one"

    @one_or_many
    def list_with_2_items():
        return ['first item', 'last one']

    expect(list_with_2_items()).to.be.a(list)
    expect(list_with_2_items()).to.equal(['first item', 'last one'])


def test_one_or_many_returning_zero():
    "@one_or_many decorator returns None if the list has 0 items"

    @one_or_many
    def empty_list():
        return []

    expect(empty_list()).to.be.none
