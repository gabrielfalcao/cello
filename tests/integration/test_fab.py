#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from cello import (
    Stage,
    Case,
    CelloStopScraping,
    CelloJumpToNextStage,
)
from sleepyhollow import SleepyHollow


class SayResultsCase(Case):
    def save(self, data):
        if not 'name' in data:
            return

        data['source'] = data.get('brand', data.get('designer', 'unknown source'))
        os.system("say '{name} by {source}'".format(**data))
        os.system("say 'its full price is {full_price} but its sale price is {sale_price}'".format(**data))
        os.system('open %s' % data['image'])
        raise CelloStopScraping


class EachFabProduct(Stage):
    case = SayResultsCase

    def play(self):
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


class EachFabBrand(Stage):
    next_stage = EachFabProduct

    def play(self):
        self.scrape(self.dom.query('a[href*="/sale/"]').attr("href").raw())


class Fab(Stage):
    url = 'http://fab.com'
    next_stage = EachFabBrand


def test_scraping():
    "Scraping from FAB"
    Fab.visit(SleepyHollow())
