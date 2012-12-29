#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json

from sure import expect

from cello import Stage, Route, Case
from sleepyhollow import SleepyHollow


class JSONFileCase(Case):
    def save(self, data):
        filename = re.sub(r'\W', '', self.stage.url) + '.json'
        with open(filename, 'w') as f:
            f.write(json.dumps(data))


class BananaRepublicProductRoute(Route):
    url_mapping = 'http://bananarepublic.gap.com/browse/product.do?pid={product_id}'
    url_regex = re.compile(r'[A-Z](?P<product_id>\d+)\.jsp')


class EachProductBananaRepublic(Stage):
    route = BananaRepublicProductRoute
    case = JSONFileCase

    def play(self):
        selector = r'a.productItemName'
        links = self.dom.query(selector).attr('href')
        self.scrape(links)

    def tune(self):
        data = {
            'image': self.dom.query('#product_image').attr('src'),
            'name': self.dom.query('#productNameText .productName').text(),
        }
        assert data['image'] is not None
        assert data['image'].endswith('jpg')
        raise ValueError('nice scraper!')


class EachCategoryBananaRepublic(Stage):
    next_stage = EachProductBananaRepublic

    def play(self):
        selector = r'ul li.idxBottomCat a'
        sale_only = lambda link: 'sale' in link
        links = filter(sale_only, self.dom.query(selector).attr('href'))
        self.scrape(links)


class BananaRepublic(Stage):
    url = "http://www.bananarepublic.com/products/index.jsp"
    next_stage = EachCategoryBananaRepublic


def test_scraping():
    "Scraping from banana republic"
    expect(BananaRepublic.visit).when.called_with(SleepyHollow()).should.throw(ValueError, 'nice scraper!')
