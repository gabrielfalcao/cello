#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os
import logging

from cello import (
    Stage,
    Route,
    Case,
    CelloStopScraping,
)
from sleepyhollow import SleepyHollow

from helpers import BANANA_REPUBLIC_SKU_SCRIPT, logger


class SayResultsCase(Case):
    def save(self, data):
        if not 'name' in data:
            return

        os.system("say '{name} of color {color_name}'".format(**data))
        os.system("say 'its full price is {full_price} but its sale price is {sale_price}'".format(**data))
        os.system("say 'opening {color_name} image so you can check it out'".format(**data))
        os.system('open %s' % data['image'])
        os.system('open %s' % data['color_url'])
        raise CelloStopScraping


class BananaRepublicProductRoute(Route):
    url_mapping = 'http://bananarepublic.gap.com/browse/product.do?pid={product_id}'
    url_regex = re.compile(r'[A-Z](?P<product_id>\d+)\.jsp')


class EachSKUBananaRepublic(Stage):
    route = BananaRepublicProductRoute
    case = SayResultsCase

    def play(self):
        self.fetch()
        product_name = self.dom.query('#productNameText .productName').text()

        try:
            skus = []
            for x in range(10):
                if (len(skus) is 0) or (not isinstance(skus, list)):
                    self.fetch()
                    skus = self.browser.evaluate_javascript(BANANA_REPUBLIC_SKU_SCRIPT)

        except Exception:
            logger.exception(
                "Could not evaluate javascript for %s (%s)",
                product_name, self.response.url)
            return

        if len(skus) is 0:
            msg = "%s out of stock: %s" % (self.url, self.response.url)
            logging.info(msg)
            return

        if not isinstance(skus, list):
            msg = "Skipping {} due a bad JSON return value: {}".format(product_name, repr(skus))
            logger.error(msg)
            return

        for sku in skus:
            sku['product_name'] = product_name
            full_data = self.prepare_sku(sku)
            self.persist(full_data)

    def prepare_sku(self, sku=None):
        data = self.tune()
        if not sku:
            return data
        data['brand'] = 'Banana Republic'
        sku['color_name'] = sku['color_name'].lower().replace("color:", "").strip()
        data.update(sku)
        data['filename'] = re.sub(r'\W+', '_', "sku {brand} {product_name} {color_name}".format(**data)) + '.json'
        return data


class EachProductBananaRepublic(Stage):
    route = BananaRepublicProductRoute
    next_stage = EachSKUBananaRepublic

    def play(self):
        selector = r'a.productItemName'
        links = self.dom.query(selector).attr('href').raw()
        self.scrape(links)


class EachCategoryBananaRepublic(Stage):
    next_stage = EachProductBananaRepublic

    def play(self):
        selector = r'ul li.idxBottomCat a[href*=sale]'
        links = self.dom.query(selector).attr('href').raw()
        self.scrape(links)


class BananaRepublic(Stage):
    url = "http://www.bananarepublic.com/products/index.jsp"
    next_stage = EachCategoryBananaRepublic


def test_scraping():
    "Scraping from banana republic"
    BananaRepublic.visit(SleepyHollow())
