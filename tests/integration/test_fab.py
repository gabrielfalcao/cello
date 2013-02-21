#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from cello import (
    Case,
    CelloJumpToNextStage,
)
from cello import MultiProcessStage as Stage


class SayResultsCase(Case):
    def save(self, data):
        print data


class EachFabProduct(Stage):
    case = SayResultsCase

    def play(self):
        print self.url
        self.scrape(self.dom.query('a[href*="/product/"]').attr("href").raw())

    def tune(self):
        keys = map(lambda x: x.lower().strip(), self.dom.query("ul.tblList .half label").text())
        values = self.dom.query("ul.tblList .half span").text()
        data = dict(zip(keys, values))

        fab_price = self.dom.query('.fabPrice').text()
        if not fab_price:
            raise CelloJumpToNextStage('not a product page')

        data['sale_price'] = fab_price[0]
        data['full_price'] = self.dom.query('.retailPrice').text()[0].split(" ")[0]
        data['name'] = self.dom.query('.prodInfoBlock h1').text()
        data['image'] = self.dom.query(
            'img[src*=png][src*=primary][data-zoom]').attr('src').one().replace('//', 'http://')

        return data


class Fab(Stage):
    url = 'http://fab.com'
    next_stage = EachFabProduct

    def play(self):
        self.fetch()
        self.scrape(self.dom.query('a[href*="/sale/"]').attr("href").raw())


def browser_factory():
    return requests

Fab.visit(browser_factory)
