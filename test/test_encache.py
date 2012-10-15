import unittest
import random
import encache
from mock import Mock
import tempfile
import os
import shutil


class Guid(object):
    "Mock object for notes and notebooks."

    def __init__(self, guid, title=None, name=None):
        self.guid = guid
        self.title = title
        self.name = name

    def __eq__(self, other):
        return self.guid == other.guid

    def __str__(self):
        return "guid: %s title=%s name=%s" % (self.guid, self.title, self.name)


class TestENCache(unittest.TestCase):

    def setUp(self):
        encache.TBinaryProtocol = Mock()
        encache.THttpClient = Mock()
        encache.UserStore = Mock()
        encache.NoteStore = Mock()
        encache.SyncChunkFilter = Mock()
        encache.UserStore.Client().getUser.return_value = Mock(id="uid")
        self.testdir = tempfile.mkdtemp()
        self.cache = encache.ENCache("token", "host", self.testdir)

    def test_createdir(self):
        user_path = os.sep.join([self.testdir, "host", "uid"])
        self.assertTrue(os.path.exists(user_path))

    def test_userpath(self):
        userpath = os.sep.join([self.testdir, "host", "uid", "user.dat"])
        self.assertEquals(self.cache.userfile_path, userpath)

    def test_sync_count(self):
        self._sync()
        self.assertEqual(self.cache.last_update_count, 5)

    def test_notes(self):
        self._sync()
        self.assertEqual(self.cache.notes, [Guid("a2", title="c1")])

    def test_notebook_map(self):
        self._sync()
        self.assertEqual(self.cache.notebook_map, {"b2": "d1"})

    def test_load_from_disk(self):
        self._sync()
        newcache = encache.ENCache("token", "host", self.testdir)
        self.assertEqual(newcache.notes, [Guid("a2", title="c1")])

    def _sync(self):
        chunk = Mock(chunkHighUSN=5, updateCount=5,
                     notes=[Guid("a1"), Guid("a2", title="c1")],
                     notebooks=[Guid("b1"), Guid("b2", name="d1")],
                     expungedNotes=["a1"],
                     expungedNotebooks=["b1"])
        self.cache.notestore.getFilteredSyncChunk.return_value = chunk
        self.cache.sync()

    def tearDown(self):
        shutil.rmtree(self.testdir)

if __name__ == '__main__':
    unittest.main()
