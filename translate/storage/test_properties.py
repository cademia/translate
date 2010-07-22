#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import properties
from translate.storage import test_monolingual
from translate.misc import wStringIO

def test_find_delimiter_pos_simple():
    assert properties.find_delimiter("key=value") == ('=', 3)
    assert properties.find_delimiter("key:value") == (':', 3)
    assert properties.find_delimiter("key value") == (' ', 3)
    assert properties.find_delimiter("= value") == ('=', 0)

def test_find_delimiter_pos_whitespace():
    assert properties.find_delimiter("key = value") == ('=', 4)
    assert properties.find_delimiter("key : value") == (':', 4)
    assert properties.find_delimiter("key   value") == (' ', 3)
    assert properties.find_delimiter("key key = value") == (' ', 3)
    assert properties.find_delimiter("key value value") == (' ', 3)
    assert properties.find_delimiter(" key = value") == ('=', 5)

def test_find_delimiter_pos_escapes():
    assert properties.find_delimiter("key\:=value") == ('=', 5)
    assert properties.find_delimiter("key\=: value") == (':', 5)
    assert properties.find_delimiter("key\   value") == (' ', 5)
    assert properties.find_delimiter("key\ key\ key\: = value") == ('=', 16)

def test_is_line_continuation():
    assert properties.is_line_continuation("") == False
    assert properties.is_line_continuation("some text") == False
    assert properties.is_line_continuation("""some text\\""") == True
    assert properties.is_line_continuation("""some text\\\\""") == False  # Escaped \
    assert properties.is_line_continuation("""some text\\\\\\""") == True  # Odd num. \ is line continuation
    assert properties.is_line_continuation("""\\\\\\""") == True

def test_key_strip():
    assert properties.key_strip("key") == "key"
    assert properties.key_strip(" key") == "key"
    assert properties.key_strip("\ key") == "\ key"
    assert properties.key_strip("key ") == "key"
    assert properties.key_strip("key\ ") == "key\ "


class TestPropUnit(test_monolingual.TestMonolingualUnit):
    UnitClass = properties.propunit

    def test_difficult_escapes(self):
        """It doesn't seem that properties files can store double backslashes.
        
        We are disabling the double-backslash tests for now.
        If we are mistaken in the above assumption, we need to fix getsource()
        and setsource() and delete this test override.
        
        """
        pass

    def test_rich_get(self):
        pass

    def test_rich_set(self):
        pass

class TestProp(test_monolingual.TestMonolingualStore):
    StoreClass = properties.propfile
    
    def propparse(self, propsource, personality="java"):
        """helper that parses properties source without requiring files"""
        dummyfile = wStringIO.StringIO(propsource)
        propfile = properties.propfile(dummyfile, personality)
        return propfile

    def propregen(self, propsource):
        """helper that converts properties source to propfile object and back"""
        return str(self.propparse(propsource))

    def test_simpledefinition(self):
        """checks that a simple properties definition is parsed correctly"""
        propsource = 'test_me=I can code!'
        propfile = self.propparse(propsource)
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == "test_me"
        assert propunit.source == "I can code!"

    def test_simpledefinition_source(self):
        """checks that a simple properties definition can be regenerated as source"""
        propsource = 'test_me=I can code!'
        propregen = self.propregen(propsource)
        assert propsource + '\n' == propregen

    def test_unicode_escaping(self):
        """check that escapes unicode is converted properly"""
        propsource = "unicode=\u0411\u0416\u0419\u0428"
        messagevalue = u'\u0411\u0416\u0419\u0428'.encode("UTF-8")
        propfile = self.propparse(propsource, personality="mozilla")
        assert len(propfile.units) == 1
        propunit = propfile.units[0]
        assert propunit.name == "unicode"
        assert propunit.source.encode("UTF-8") == "БЖЙШ"
        regensource = str(propfile)
        assert messagevalue in regensource
        assert "\\u" not in regensource

    def test_newlines_startend(self):
        """check that we preserve \n that appear at start and end of properties"""
        propsource = "newlines=\\ntext\\n"
        propregen = self.propregen(propsource)
        assert propsource + '\n' == propregen

    def test_whitespace_handling(self):
        """check that we remove extra whitespace around property"""
        whitespaces = (('key = value', 'key', 'value'),      # Standard for baseline
                       (' key =  value', 'key', 'value'),    # Extra \s before key and value
                       ('\ key\ = value', '\ key\ ', 'value'), # extra space at start and end of key
                       ('key = \ value ', 'key', ' value '), # extra space at start end end of value
                      )
        for propsource, key, value in whitespaces:
            propfile = self.propparse(propsource)
            propunit = propfile.units[0]
            print repr(propsource), repr(propunit.name), repr(propunit.source)
            assert propunit.name == key
            assert propunit.source == value
     
    def test_key_value_delimiters_simple(self):
        """test that we can handle colon, equals and space delimiter
        between key and value.  We don't test any space removal or escaping"""
        delimiters = [":", "=", " "]
        for delimiter in delimiters:
            propsource = "key%svalue" % delimiter
            print "source: '%s'\ndelimiter: '%s'" % (propsource, delimiter)
            propfile = self.propparse(propsource)
            assert len(propfile.units) == 1
            propunit = propfile.units[0]
            assert propunit.name == "key"
            assert propunit.source == "value"

    def test_comments(self):
        """checks that we handle # and ! comments"""
        markers = ['#', '!']
        for comment_marker in markers:
            propsource = '''%s A comment
key=value
''' % comment_marker
            propfile = self.propparse(propsource)
            print repr(propsource)
            print "Comment marker: '%s'" % comment_marker
            assert len(propfile.units) == 1
            propunit = propfile.units[0]
            assert propunit.comments == ['%s A comment' % comment_marker]

    def test_latin1(self):
        """checks that we handle non-escaped latin1 text"""
        prop_source = u"key=valú".encode('latin1')
        prop_store = self.propparse(prop_source)
        assert len(prop_store.units) == 1
        unit = prop_store.units[0]
        assert unit.source == u"valú"

    def test_fullspec_delimiters(self):
        """test the full definiation as found in Java docs"""
        proplist = ['Truth = Beauty\n', '       Truth:Beauty', 'Truth                  :Beauty', 'Truth        Beauty']
        for propsource in proplist:
            propfile = self.propparse(propsource)
            propunit = propfile.units[0]
            print propunit
            assert propunit.name == "Truth"
            assert propunit.source == "Beauty"

    def xtest_fullspec_escaped_key(self):
        """Escaped delimeters can be in the key"""
        prop_source = u"\:\="
        prop_store = self.propparse(prop_source)
        assert len(prop_store.units) == 1
        unit = prop_store.units[0]
        print unit
        assert unit.name == u":="

    def test_fullspec_line_continuation(self):
        """Whitespace delimiter and pre whitespace in line continuation are dropped"""
        prop_source = ur"""fruits                           apple, banana, pear, \
                                  cantaloupe, watermelon, \
                                  kiwi, mango
"""
        prop_store = self.propparse(prop_source)
        assert len(prop_store.units) == 1
        unit = prop_store.units[0]
        print unit
        assert properties.find_delimiter(prop_source) == (' ', 6)
        assert unit.name == u"fruits"
        assert unit.source == u"apple, banana, pear, cantaloupe, watermelon, kiwi, mango"

    def xtest_fullspec_key_without_value(self):
        """A key can have no value in which case the value is the empty string"""
        prop_source = u"cheeses"
        prop_store = self.propparse(prop_source)
        assert len(prop_store.units) == 1
        unit = prop_store.units[0]
        print unit
        assert unit.name == u"cheeses"
        assert unit.source == u""
