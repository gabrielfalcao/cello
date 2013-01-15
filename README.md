```shell
                   ,,    ,,
                 `7MM  `7MM
                   MM    MM
 ,p6"bo   .gP"Ya   MM    MM  ,pW"Wq.
6M'  OO  ,M'   Yb  MM    MM 6W'   `Wb
8M       8M""""""  MM    MM 8M     M8
YM.    , YM.    ,  MM    MM YA.   ,A9
 YMbmd'   `Mbmmd'.JMML..JMML.`Ybmd9'
```
# version 0.0.3
![https://raw.github.com/Yipit/cello/master/icon.png?login=gabrielfalcao&token=837b128ca9c4b1f3cb8e57457238ce38](https://raw.github.com/Yipit/cello/master/icon.png?login=gabrielfalcao&token=837b128ca9c4b1f3cb8e57457238ce38)


# Installation

```shell
pip install -i "http://localshop.staging.yipit.com/simple/" cello
```

# Hacking on it

```shell
mkvirtualenv cello
git clone git@github.com:Yipit/cello.git
cd cello
pip install -r requirements.pip
make unit
make integration
```

# Tutorial

Let's write our first scraper using Fab.com as an example.

Each part of this tutorial shows an example code, the latest example is
always a working code, and because of that there is a lot of repeated
code.

## 1. Create stages

Create a python file called `fab_scraper.py` with the following
contents:

```python
from cello import Stage
```

### 1.1. The initial stage

The initial stage is just a `Stage` class that contains a url and the
next step.

```python
from cello import Stage

class Fab(Stage):
    url = 'http://fab.com'
```

### 1.2. The second stage

The second stage will find links containing `/sale/` in its `href`
attribute and scrape them.

Notice that we also change the first stage to point `next_stage` to be
the "brand scraping" stage.

```python
from cello import Stage

class EachFabBrand(Stage):
    def play(self):
        self.scrape(self.dom.query('a[href*="/sale/"]').attr("href").raw())


class Fab(Stage):
    url = 'http://fab.com'
    next_stage = EachFabBrand
```


### 1.3. The last stage

The last stage is the product itself, we will find products in the
current category by implementing the `play(self)` method again, but
now it is looking for links containing `/product/` in the `href`
attribute.

Also, because it is the last stage it differs from the previous stages
in two ways:

1. It doesn't specify a `next_stage`, of course.

2. It implements a `tune(self)` method that must return a dictionary of product data (name, price, brand, etc)

```python
from cello import Stage, CelloJumpToNextStage

class EachFabProduct(Stage):
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
```

## 2. Persisting data

At this point you have all components of the scraper system set up,
but where will it be stored?

Cello has a concept of `Case`. Imagine you finish playing a Cello, you
must store it in its case.

### A hypothetical Django-based case

```python
from cello import Case

class DataModelCase(Case):
   def save(self, data):
       # the line below is the only coupling point with Django
       from shop.models import Product
       Product.objects.get_or_create(**data)
```

### A filesystem-based case for Fab.com

Here is a working example of a case for our Fab products.

```python
import re
import json
from cello import Stage

class FilesystemCase(Case):
    def save(self, data):
        filename = re.sub(r'\W', '_', data['url']) + '.json'
        with open(filename, 'w') as f:
            f.write(json.dumps(data))
            print "saved", filename
```

## 3. Running a scraper with SleepyHollow

Cello is not only 100% decoupled from Django, but it's also loosely
coupled with SleepyHollow.

To run a scraper, call the method `.visit()` First stage passing an
instance of SleepyHollow

```python

from sleepyhollow import SleepyHollow as Browser
Fab.visit(Browser())
```


# All together

Your first scraper

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
from sleepyhollow import SleepyHollow as Browser
from cello import Stage, Case, CelloJumpToNextStage


class FilesystemCase(Case):
    def save(self, data):
        filename = re.sub(r'\W', '_', data['url']) + '.json'
        with open(filename, 'w') as f:
            f.write(json.dumps(data))
            print "saved", filename


class EachFabProduct(Stage):
    case = FilesystemCase

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

Fab.visit(Browser())
````

# See it working

You can download it here [https://www.dropbox.com/s/icfbx9eft97h8co/Cello.mov](https://www.dropbox.com/s/icfbx9eft97h8co/Cello.mov)
