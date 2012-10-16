import re


class Tokeniser(object):
    """Simple tokeniser."""

    regexp = re.compile(r'''(?x)
        \$?\d+(?:\.\d+)?     # currency amounts, e.g. $12.50
        | (?:[A-Z]\.)+       # abbreviations, e.g. U.S.A.
        | [^\w\s]+           # sequences of punctuation
        | [\w-]+             # sequences of word characters
    ''', re.UNICODE)

    @classmethod
    def split(cls, string):
        """Split the input string into tokens.

        Args:
            string: A single-line or multi-line string.

        Returns:
            List of tokens.
        """
        return cls.regexp.findall(string)
