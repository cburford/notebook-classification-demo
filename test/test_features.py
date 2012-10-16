# -*- coding: utf-8 -*-

import unittest
import features
import tempfile
from mock import Mock
from evernote.edam.type.ttypes import Note, NoteAttributes
import shutil
from StringIO import StringIO


class TestFeatures(unittest.TestCase):

    def test_full_metadata(self):
        note = Note()
        note.title = "test title"
        attributes = NoteAttributes()
        note.attributes = attributes
        attributes.sourceURL = "https://testdomain/some/path"
        attributes.latitude = 1
        attributes.source = "testsource"
        attributes.placeName = "testplace"
        attributes.contentClass = "testclass"
        featuredict = {}
        features.add_metadata_features(featuredict, note)
        expected_keys = ("META-TITLETOKEN-test", "META-TITLETOKEN-title",
                         "META-URL-testdomain", "META-HASURL",
                         "META-HASLOCATION", "META-SOURCE-testsource",
                         "META-PLACE-testplace", "META-CONTENTCLASS-testclass")
        expected = dict.fromkeys(expected_keys, 1)
        self.assertEqual(featuredict, expected)

    def test_base_metadata(self):
        note = Note()
        note.title = "test title"
        note.attributes = NoteAttributes()
        featuredict = {}
        features.add_metadata_features(featuredict, note)
        expected_keys = ("META-TITLETOKEN-test", "META-TITLETOKEN-title")
        expected = dict.fromkeys(expected_keys, 1)
        self.assertEqual(featuredict, expected)

    def test_basic_content(self):
        content = StringIO("<en-note><div>Hi there</div></en-note>")
        expected_keys = ("CONTENT-TOKEN-hi", "CONTENT-TOKEN-there")
        expected = dict.fromkeys(expected_keys, 1)
        featuredict = {}
        features.add_content_features(featuredict, content)
        self.assertEqual(featuredict, expected)

    def test_complex_content(self):
        content = StringIO("<en-note><div>Hi <b>there</b> friend</div>"
                           "<div> Hi</div>"
                           "</en-note>")
        expected_keys = ("CONTENT-TOKEN-hi", "CONTENT-TOKEN-there",
                         "CONTENT-TOKEN-friend")
        expected = dict.fromkeys(expected_keys, 1)
        featuredict = {}
        features.add_content_features(featuredict, content)
        self.assertEqual(featuredict, expected)

    def test_empty_content(self):
        content = StringIO("<en-note><div> <b> </b> </div>"
                           "</en-note>")
        featuredict = {}
        features.add_content_features(featuredict, content)
        self.assertEqual(featuredict, {})

    def test_full_content(self):
        content = StringIO('<en-note><div>test</div> '
                           '<en-media type="image/jpeg"/>'
                           '<en-todo/>'
                           '<a href="http://test1/path">link1</a> '
                           '<a href="http://test2/path">link2</a> '
                           '<a>link3</a>'
                           '<en-media type="image/png"/>'
                           '</en-note>')
        expected_keys = ("CONTENT-TOKEN-test", "CONTENT-TOKEN-link1",
                         "CONTENT-TOKEN-link2", "CONTENT-TOKEN-link3",
                         "CONTENT-LINK-test1", "CONTENT-LINK-test2",
                         "CONTENT-TODO", "CONTENT-MEDIA-image/jpeg",
                         "CONTENT-MEDIA-image/png", "CONTENT-HASLINK")
        expected = dict.fromkeys(expected_keys, 1)
        featuredict = {}
        features.add_content_features(featuredict, content)
        self.assertEqual(featuredict, expected)

    def test_entities(self):
        content = StringIO('<en-note><div>test &gt;</div>'
                           '<div>test&nbsp;test2</div></en-note>')
        expected_keys = ("CONTENT-TOKEN-test", "CONTENT-TOKEN-test2",
                         "CONTENT-TOKEN->")
        expected = dict.fromkeys(expected_keys, 1)
        featuredict = {}
        features.add_content_features(featuredict, content)
        self.assertEqual(featuredict, expected)

    def test_unicode(self):
        string = ('<?xml version="1.0" encoding="UTF-8"?>'
                  '<!DOCTYPE en-note SYSTEM '
                  '"http://xml.evernote.com/pub/enml.dtd">'
                  u'<en-note><div>hi abcdé</div></en-note>')
        content = StringIO(string.encode("utf-8"))
        expected_keys = ("CONTENT-TOKEN-hi", u"CONTENT-TOKEN-abcdé")
        expected = dict.fromkeys(expected_keys, 1)
        featuredict = {}
        features.add_content_features(featuredict, content)
        self.assertEqual(featuredict, expected)

if __name__ == '__main__':
    unittest.main()
