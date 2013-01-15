#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import logging
from datetime import datetime
from cello import Case


logger = logging.getLogger('cello')
logger.addHandler(logging.FileHandler(datetime.now().strftime('cello-%Y-%m-%d.log')))

BANANA_REPUBLIC_SKU_SCRIPT = '''(function(){
    var elements = document.querySelectorAll("#colorSwatchContent input[type=image]");
    var ret = [];
    for (var i in elements) {
        var data = {};
        var e = elements[i];

        if (!e.nodeName){
            continue;
        }

        try {
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
        } catch (e){
            continue;
        }
    }
    return ret;
})();'''


class FileCase(Case):
    def save(self, data):
        if not 'filename' in data:
            return

        filename = data['filename']
        if os.path.exists(filename):
            return

        with open(filename, 'w') as f:
            try:
                f.write(json.dumps(data))
                print "saved", filename
            except Exception:
                logger.exception("Could not write file %s because data is not json deserializable", filename)
