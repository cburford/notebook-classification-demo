import unittest
import random
import encache
from mock import Mock
import tempfile
import os
import shutil


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

    def test_testsync(self):
        chunk = Mock(chunkHighUSN=5, updateCount=5,
                     notes=None,
                     notebooks=None, expungedNotes=None,
                     expungedNotebooks=None)
        self.cache.notestore.getFilteredSyncChunk.return_value = chunk
        #print "(%s)" % self.cache.notestore.getFilteredSyncChunk().chunkHighUSN
        self.cache.sync()
        self.assertEqual(self.cache.last_update_count, 5)

    def tearDown(self):
        shutil.rmtree(self.testdir)

if __name__ == '__main__':
    unittest.main()
