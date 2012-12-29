#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re


class InvalidURLMapping(Exception):
    pass


class Route(object):
    re = re

    url_mapping = '{url}'
    url_regex = re.compile(r'^(?P<url>.*)$')

    @classmethod
    def translate(self, url):
        found = self.url_regex.search(url)

        if not found:
            raise InvalidURLMapping(
                'url {} does not match pattern {}'.format(
                    url, self.url_regex.pattern))

        return self.url_mapping.format(**found.groupdict())
