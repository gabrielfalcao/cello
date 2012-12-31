#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os

from sure import expect
from cello import Stage, Route, Case
from sleepyhollow import SleepyHollow


class SayResultsCase(Case):
    def save(self, data):
        os.system('say %s' % data['name'])
        os.system('open %s' % data['url'])
        raise ValueError('awesome')


class BananaRepublicProductRoute(Route):
    url_mapping = 'http://bananarepublic.gap.com/browse/product.do?pid={product_id}'
    url_regex = re.compile(r'[A-Z](?P<product_id>\d+)\.jsp')


class EachProductBananaRepublic(Stage):
    route = BananaRepublicProductRoute
    case = SayResultsCase

    def play(self):
        selector = r'a.productItemName'
        links = self.dom.query(selector).attr('href').raw()
        self.scrape(links)

    def tune(self):
        data = {
            'image': self.dom.query('#product_image').attr('src').raw(),
            'name': self.dom.query('#productNameText .productName').text(),
        }
        assert data['image'].lower().endswith('jpg')
        return data


class EachCategoryBananaRepublic(Stage):
    next_stage = EachProductBananaRepublic

    def play(self):
        selector = r'ul li.idxBottomCat a'
        sale_only = lambda link: 'sale' in link
        links = filter(sale_only, self.dom.query(selector).attr('href').raw())
        self.scrape(links)


class BananaRepublic(Stage):
    url = "http://www.bananarepublic.com/products/index.jsp"
    next_stage = EachCategoryBananaRepublic


def test_scraping():
    "Scraping from banana republic"
    expect(BananaRepublic.visit).when.called_with(
        SleepyHollow()).to.throw('awesome')
