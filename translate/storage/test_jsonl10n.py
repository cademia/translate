# -*- coding: utf-8 -*-

import sys
from io import BytesIO
from translate.storage import jsonl10n, test_monolingual

import pytest


class TestJSONResourceUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = jsonl10n.JsonUnit


class TestJSONResourceStore(test_monolingual.TestMonolingualUnit):
    StoreClass = jsonl10n.JsonFile

    def test_serialize(self):
        store = jsonl10n.JsonFile()
        store.parse('{"key": "value"}')
        out = BytesIO()
        src = store.serialize(out)

        assert out.getvalue() == b'{\n    "key": "value"\n}\n'

    @pytest.mark.skipif(sys.version_info < (2, 7),
                        reason="json.loads() can't order in Python 2.6")
    def test_ordering(self):
        store = jsonl10n.JsonFile()
        store.parse('''{
    "foo": "foo",
    "bar": "bar",
    "baz": "baz"
}''')

        assert store.units[0].source == 'foo'
        assert store.units[2].source == 'baz'
