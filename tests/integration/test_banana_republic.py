#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import os

from cello import Stage, Route, Case, CelloStopScraping
from sleepyhollow import SleepyHollow


class SayResultsCase(Case):
    def save(self, data):
        if not 'name' in data:
            return

        os.system("say '{name} of color {color_name}'".format(**data))
        os.system("say 'its full price is {full_price} but its sale price is {sale_price}'".format(**data))
        os.system("say 'opening {color_name} image so you can check it out'".format(**data))
        os.system('open %s' % data['image'])
        os.system('open %s' % data['color_name'])
        raise CelloStopScraping


class BananaRepublicProductRoute(Route):
    url_mapping = 'http://bananarepublic.gap.com/browse/product.do?pid={product_id}'
    url_regex = re.compile(r'[A-Z](?P<product_id>\d+)\.jsp')


class EachSKUBananaRepublic(Stage):
    route = BananaRepublicProductRoute
    case = SayResultsCase

    def play(self):
        skus = self.browser.evaluate_javascript('''(function(){
            var elements = document.querySelectorAll("#colorSwatchContent input[type=image]");
            var ret = [];
            for (var i in elements) {
                var data = {};
                var e = elements[i];

                if (!e.nodeName){
                    continue;
                }

                var focus = document.createEvent("HTMLEvents");
                focus.initEvent("dataavailable", true, true);
                focus.eventName = "focus";
                var mouseover = document.createEvent("HTMLEvents");
                mouseover.initEvent("dataavailable", true, true);
                mouseover.eventName = "mouseover";

                e.click();
                e.onfocus(focus);
                e.onmouseover(mouseover);
                data["image"] = document.querySelector("#product_image").getAttribute("src");

                data["color_url"] = e.getAttribute("src");
                data["color_name"] = document.querySelector("div.swatchLabelName").innerText;

                data["full_price"] = document.querySelector("#priceText strike").innerHTML;
                data["sale_price"] = document.querySelector("#priceText span.salePrice").innerHTML;

                ret.push(data);
            }
            return ret;
        })();''')
        data = {
            'name': self.dom.query('#productNameText .productName').text(),
        }
        if not isinstance(skus, list):
            raise TypeError("SKUS are %r" % skus)

        for sku in skus:
            full_data = data.copy()
            sku['color_name'] = sku['color_name'].lower().replace("color:", "").strip()
            full_data.update(sku)
            self.persist(full_data)


class EachProductBananaRepublic(Stage):
    route = BananaRepublicProductRoute
    next_stage = EachSKUBananaRepublic

    def play(self):
        selector = r'a.productItemName'
        links = self.dom.query(selector).attr('href').raw()
        self.scrape(reversed(links))


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
    BananaRepublic.visit(SleepyHollow())
