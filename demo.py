#!/usr/bin/env python

"""Evernote notebook classifier demo."""

from encache import ENCache
import argparse
import logging
import random
import features
from classifier import SvmClassifier
from prettytable import PrettyTable
from datetime import datetime


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
    features.add_metadata_features(featuredict, note)
    if note.attributes.contentClass is None:
        features.add_content_features(featuredict, content)
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
