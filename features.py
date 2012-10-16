"Functions for generating features from Notes."

from urlparse import urlparse
from lxml import etree
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
    parser = etree.HTMLParser()
    root = etree.parse(content, parser).getroot()
    string_content = unicode(root.xpath('string()'))
    #import html2text
    #h = html2text.HTML2Text()
    #h.ignore_images = True
    #h.ignore_links = True
    #h.ignore_emphasis = True
    #string_content = h.handle(etree.tostring(root))
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
