#!/usr/bin/env python

"Evernote notebook classifier demo."

from encache import ENCache
import argparse
import logging
import random
from classifier import SvmClassifier
from collections import Counter
from urlparse import urlparse
from lxml import etree
from prettytable import PrettyTable
from datetime import datetime


def add_metadata_features(featuredict, note):
    """Adds features from Note metadata."""
    for token in note.title.split():
        featuredict["META-TITLETOKEN-%s" % token] = 1
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
    """Adds features based on note content."""
    parser = etree.XMLParser(resolve_entities=False)
    root = etree.parse(content, parser).getroot()
    string_content = unicode(root.xpath('string()'))
    for token in string_content.split():
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


def note_features(note, content):
    """
    BOW
    BOW title
    URL domain
    has_location
    source
    place_name
    content_class

    contains_image
    contains_todo
    link domains
    resource_text
    (case folding)
    """
    featuredict = {"DEFAULT": 1}
    add_metadata_features(featuredict, note)
    if note.attributes.contentClass is None:
        add_content_features(featuredict, content)
    return featuredict


def list_notebooks(encache):
    "Print the notebook GUIDs in Evernote."
    guids = set()
    for note in encache.notes:
        guids.add(note.notebookGuid)
    print guids


def dataset_breakdown(featuresets):
    "Get stats for a dataset."
    counter = Counter()
    for _, label in featuresets:
        counter[label] += 1
    print counter.most_common()


def execute(auth_token, host, do_randomise, test_set_size, cache_dir):
    "Test code."
    # So the encache object can output progress information to the console.
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    encache = ENCache(auth_token, host, cache_root=cache_dir)
    #encache = ENCache(auth_token, evernote_host, cache_root="./data",
    #                  forceuser="195154")
    #encache.update_notes()
    #exit(1)
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
        featureset = (note_features(note, encache.note_content(note)),
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
        title = note.title
        if len(title) > max_title_len:
            title = "%s..." % title[:max_title_len - 3]
        table.add_row((title, nb_map[note.notebookGuid], nb_map[label],
                       updated))
    print table


def test():
    "Run with some test arguments."
    #auth_token = "S=s52:U=55ae32:E=141b91e237d:C=13a616cf77d:\
#P=1cd:A=en-devtoken:H=a0aa8e914b02305c4a27497f3a734424"
    auth_token = "S=s1:U=2fa52:E=1413521767b:C=139dd704a7b:P=1cd:\
A=en-devtoken:H=72141f6b92e70d8b9fba41d57b9a60e0"
    #host = "www.evernote.com"
    host = "sandbox.evernote.com"
    do_randomise = False
    test_set_size = 20
    cache_dir = "./data"
    execute(auth_token, host, do_randomise, test_set_size, cache_dir)


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
    #test()
