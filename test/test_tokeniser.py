import unittest
import random
from tokeniser import Tokeniser

class TestTokeniser(unittest.TestCase):

    def test_muliline(self):
        tokens = Tokeniser.split("hi there\nsecond line")
        self.assertEqual(tokens, ["hi", "there", "second", "line"])

    def test_currency(self):
        tokens = Tokeniser.split("hi there $100 man")
        self.assertEqual(tokens, ["hi", "there", "$100", "man"])

    def test_punctuation(self):
        tokens = Tokeniser.split("hi there, you ...")
        self.assertEqual(tokens, ["hi", "there", ",", "you", "..."])

    def test_unicode(self):
        tokens = Tokeniser.split(u'hi ther\xe9')
        self.assertEqual(tokens, ["hi", u'ther\xe9'])

if __name__ == '__main__':
    unittest.main()
