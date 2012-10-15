#!/usr/bin/env python

"""Evernote notebook classifier demo.

TODO:
consider adding feature selection
consider adding test code
consider adding resource features
"""

from encache import ENCache
import argparse
import logging
import random
from classifier import SvmClassifier
from urlparse import urlparse
from lxml import etree
from prettytable import PrettyTable
from datetime import datetime
from tokeniser import Tokeniser


def add_metadata_features(featuredict, note):
    """Add features from note metadata.

    Derive the following features from the Note and add them to the
    featuredict with binary values:

        META-TITLETOKEN-<token>: Set for each unique, case-folded token in
            the note title.
        META-URL-<domain>: Set with the domain of the note URL, if one is
            provided.
        META_HASURL: Set if the note has a URL.
        META-HASLOCATION: Set if the note has a latitude.
        META-SOURCE-<source>: Set with the source of the note, if it is
            provided.
        META-PLACE-<place>: Set with the place name of the note, if it is
            provided.
        META-CONTENTCLASS-<class>: Set with the content class of the note, if
            it is provided.

    Args:
        featuredict: A dict.
        note: Note object.
    """
    for token in Tokeniser.split(unicode(note.title, encoding="utf-8")):
        featuredict["META-TITLETOKEN-%s" % token.lower()] = 1
    if note.attributes.sourceURL:
        netloc = urlparse(note.attributes.sourceURL).netloc
        if netloc:
            featuredict["META-URL-%s" % netloc] = 1
            featuredict["META-HASURL"] = 1
    if note.attributes.latitude is not None:
        featuredict["META-HASLOCATION"] = 1
    if note.attributes.source:
        featuredict["META-SOURCE-%s" % note.attributes.source] = 1
    if note.attributes.placeName:
        featuredict["META-PLACE-%s" % note.attributes.placeName] = 1
    if note.attributes.contentClass:
        featuredict["META-CONTENTCLASS-%s" % note.attributes.contentClass] = 1


def add_content_features(featuredict, content):
    """Add features from note content.

    Derive the following features from the Note and add them to the
    featuredict with binary values:

        CONTENT-TOKEN-<token>: Set for each unique, case-folded token in the
            note content (not including markup).
        CONTENT-MEDIA-<mimetype>: Set for each mimetype used for media in the
            note.
        CONTENT-HASLINK: Set if the note contains one or more links.
        CONTENT-LINK-<domain>: Set with the domain of each link in the note.
        CONTENT-TODO: Set if the note contains a todo.

    Args:
        featuredict: A dict.
        content: File-like object containing the note content.
    """
    #parser = etree.XMLParser(resolve_entities=False)
    parser = etree.HTMLParser()
    root = etree.parse(content, parser).getroot()
    string_content = unicode(root.xpath('string()'))
    #print string_content.encode("utf-8")
    for token in Tokeniser.split(string_content):
        featuredict["CONTENT-TOKEN-%s" % token.lower()] = 1
    for media in root.iterfind(".//en-media"):
        featuredict["CONTENT-MEDIA-%s" % media.get("type")] = 1
    for link in root.iterfind(".//a"):
        url = link.get("href")
        if url is not None:
            featuredict["CONTENT-HASLINK"] = 1
            netloc = urlparse(link.get("href")).netloc
            if netloc:
                featuredict["CONTENT-LINK-%s" % netloc] = 1
    if root.find(".//en-todo") is not None:
        featuredict["CONTENT-TODO"] = 1


def note_featuredict(note, content):
    """Generate a featuredict.

    Args:
        note: Note object.
        content: File-like object containing the note content.

    Returns:
        A dictionary where keys are feature names and values are feature
        values.
    """
    featuredict = {"DEFAULT": 1}
    add_metadata_features(featuredict, note)
    if note.attributes.contentClass is None:
        add_content_features(featuredict, content)
    return featuredict


def execute(auth_token, host, do_randomise, test_set_size, cache_dir):
    """Execute the demo and print output to the console.

    Args:
        auth_token: A string.
        host: "www.evernote.com" or "sandbox.evernote.com".
        do_randomise: Boolean indicating whether or not to shuffle the list
            of notes before creating training and test sets.
        test_set_size: Number of notes to reserve for the test set.
        cache_dir: Root location for the Evernote cache.
    """
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    encache = ENCache(auth_token, host, cache_root=cache_dir)
    encache.sync()
    notes = list(encache.notes)
    print "%d notes in account" % len(encache.notes)
    if len(notes) <= test_set_size:
        print "please specify a smaller test set size"
        exit(1)
    if do_randomise:
        random.shuffle(notes)
    featuresets = []
    for note in notes:
        featureset = (note_featuredict(note, encache.note_content(note)),
                      note.notebookGuid)
        featuresets.append(featureset)
    featuresets_tr = featuresets[:-test_set_size]
    featuresets_t = featuresets[-test_set_size:]
    classifier = SvmClassifier.train(featuresets_tr)
    print "using %d features" % len(classifier.featureindex)
    labels = classifier.classify(featuresets_t)
    nb_map = encache.notebook_map
    table = PrettyTable(["note", "actual", "predicted", "updated"])
    max_title_len = 30
    for note, label in zip(notes[-test_set_size:], labels):
        dtime = datetime.fromtimestamp(note.updated / 1000)
        updated = dtime.strftime("%Y%m%d %H:%M")
        row = [note.title, nb_map[note.notebookGuid], nb_map[label], updated]
        # Work around EDAM encoding bug.
        for i, value in enumerate(row):
            row[i] = unicode(value, encoding="utf-8")
        if len(row[0]) > max_title_len:
            row[0] = "%s..." % row[0][:max_title_len - 3]
        table.add_row(row)
    print table


def run_cli():
    """Process a command line execution."""
    parser = argparse.ArgumentParser(description="Evernote notebook \
classification demo")
    parser.add_argument("auth_token", help="authentication token")
    parser.add_argument("-s", default="sandbox.evernote.com",
                        help="server (default: sandbox.evernote.com)", )
    parser.add_argument("-n", help="number of notes to classify (default: 5)",
                        type=int, default=5)
    parser.add_argument("-d", help="cache directory (default: ./data)",
                        default="./data")
    parser.add_argument("-r", action="store_true",
                        help="shuffles notes so the test set is random")
    args = parser.parse_args()
    execute(args.auth_token, args.s, args.r, args.n, args.d)


if __name__ == "__main__":
    run_cli()
