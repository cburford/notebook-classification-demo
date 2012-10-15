import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.notestore.NoteStore as NoteStore
from evernote.edam.notestore.ttypes import SyncChunkFilter
import os
import pickle
from collections import OrderedDict
import logging


class ENCache(object):
    """A read-only cache of note and notebook data.

    Content is stored in a specified cache directory under the sub-path
    <evernote_host>/<username_id>.

    Note contents are stored in flat, utf-8 encoded files named with the
    note GUID.

    EDAM Note and Notebook objects and the last update count are stored as a
    pickled dictionary with the filename 'user.dat' and the form:

    { "last_update_count": VALUE,
      "notes": OrderedDict([(GUID, NOTE), (GUID, NOTE), ...]),
      "notebooks": OrderedDict([(GUID, NOTEBOOK), (GUID, NOTEBOOK), ...)])

    The full set of Note objects (not note contents) is managed in memory
    and re-written to disk after each call to sync, so don't use this in high
    performance scenarios.

    Attributes:
        notestore: NoteStore object.
        userstore: UserStore object.
        last_update_count: The last USN successfully synced.
        notes: List of Note objects, ordered by ascending USN.
        notebooks: List of Notebook objects, ordered by ascending USN.
        notebook_map: Mapping from Notebook GUIDs to titles.
        auth_token: As passed to __init__.
        cache_path: Path to the cache directory for the user.
        dat_path: Path to the user.dat file for the user.
        user_id: The numeric user ID.

    Raises:
        In addition to the exceptions listed, all methods can raise either of:
            EDAMUserException: Auth failed or invalid request.
            EDAMSystemException: Server-side error.
    """

    USERFILE_NAME = "user.dat"
    MAX_SYNC_OBJS = 256  # This is the maximum. See EDAM docs.

    def __init__(self, auth_token, host, cache_root="data"):
        """Connect to the API and read any cached notes and notebooks into
        memory.

        Args:
            auth_token: A string.
            host: "www.evernote.com" or "sandbox.evernote.com".
            cache_root: Path to cache root directory.

        Raises:
            IOError: Connection or name resolution failed, or cache access
                error.
        """
        # Get the UserStore object and user ID.
        userstore_uri = "https://%s/edam/user" % host
        userstore_httpclient = THttpClient.THttpClient(userstore_uri)
        userstore_protocol = \
            TBinaryProtocol.TBinaryProtocol(userstore_httpclient)
        userstore = UserStore.Client(userstore_protocol)
        user_id = userstore.getUser(auth_token).id
        # Get the NoteStore object.
        notestore_url = userstore.getNoteStoreUrl(auth_token)
        notestore_httpclient = THttpClient.THttpClient(notestore_url)
        notestore_protocol = \
            TBinaryProtocol.TBinaryProtocol(notestore_httpclient)
        notestore = NoteStore.Client(notestore_protocol)
        # Prepare the cache and set attributes.
        cache_path = os.path.sep.join([cache_root, host, str(user_id)])
        userfile_path = os.path.sep.join([cache_path, self.USERFILE_NAME])
        if os.path.exists(userfile_path):
            cdata = pickle.load(open(userfile_path))
            self.note_data = cdata["note_data"]
            self.notebook_data = cdata["notebook_data"]
            self.last_update_count = cdata["last_update_count"]
        else:
            if not os.path.exists(cache_path):
                os.makedirs(cache_path)
            self.note_data = OrderedDict()
            self.notebook_data = OrderedDict()
            self.last_update_count = 0
        self.userstore = userstore
        self.notestore = notestore
        self.auth_token = auth_token
        self.user_id = user_id
        self.cache_path = cache_path
        self.userfile_path = userfile_path
        self.logger = logging.getLogger("ENCache")
        self.logger.debug("connected")

    @property
    def notes(self):
        """Get the list of Notes, ordered by ascending USN."""
        return self.note_data.values()

    @property
    def notebooks(self):
        """Get the list of Notebooks, ordered by ascending USN."""
        return self.notebook_data.values()

    @property
    def notebook_map(self):
        """Get a mapping from Notebook GUIDs to titles."""
        return dict([(nb.guid, nb.name) for nb in self.notebooks])

    def _write_userfile(self):
        """Write the userfile to the cache."""
        self.logger.debug("writing to cache")
        cdata = {"note_data": self.note_data,
                 "notebook_data": self.notebook_data,
                 "last_update_count": self.last_update_count}
        pickle.dump(cdata, open(self.userfile_path, "w"))

    def sync(self):
        """Synchronise with the server.

        Read new and updated Note and Notebook objects. Delete expunged Notes
        and Notebooks.

        Note content for new and updated Notes is deleted if it already
        exists in the cache, but it is not downloaded.

        Raises:
            IOError: Cache access error.
        """
        scfilter = SyncChunkFilter(includeNotes=True,
                                   includeNoteAttributes=True,
                                   includeNotebooks=True,
                                   includeExpunged=True)
        after_usn = self.last_update_count
        while True:
            chunk = self.notestore.getFilteredSyncChunk(self.auth_token,
                                                        after_usn,
                                                        self.MAX_SYNC_OBJS,
                                                        scfilter)
            if chunk.chunkHighUSN:
                after_usn = chunk.chunkHighUSN
                if chunk.notes:
                    for note in chunk.notes:
                        if note.guid in self.note_data:
                            self.logger.debug("updating note %s", note.guid)
                            del self.note_data[note.guid]
                            self._clear_note_content(note.guid)
                        else:
                            self.logger.debug("adding note %s", note.guid)
                        self.note_data[note.guid] = note
                if chunk.notebooks:
                    for notebook in chunk.notebooks:
                        if notebook.guid in self.notebook_data:
                            self.logger.debug("updating notebook %s",
                                              notebook.guid)
                            del self.notebook_data[notebook.guid]
                        else:
                            self.logger.debug("adding notebook %s",
                                              notebook.guid)
                        self.notebook_data[notebook.guid] = notebook
                if chunk.expungedNotes:
                    for guid in chunk.expungedNotes:
                        if guid in self.note_data:
                            self.logger.debug("expunging note %s", guid)
                            self._clear_note_content(guid)
                            del self.note_data[guid]
                if chunk.expungedNotebooks:
                    for guid in chunk.expungedNotebooks:
                        if guid in self.notebook_data:
                            self.logger.debug("expunging notebook %s", guid)
                            del self.notebook_data[guid]
                self.logger.debug("synced %d/%d", chunk.chunkHighUSN,
                                  chunk.updateCount)
                if after_usn == chunk.updateCount:
                    break
            else:
                break
        if after_usn != self.last_update_count:
            self.last_update_count = after_usn
            self._write_userfile()

    def _note_content_fname(self, guid):
        """Get the cache filename for the given note.

        Args:
            note: A Note GUID.

        Returns:
            Path string.
        """
        return os.path.sep.join([self.cache_path, guid])

    def _clear_note_content(self, guid):
        """Clear the content from the cache for a note.

        Args:
            note: A Note GUID.
        """
        fname = self._note_content_fname(guid)
        try:
            os.unlink(fname)
        except IOError:
            pass

    def note_content(self, note):
        """Get the content of the given note.

        Args:
            note: Note object.

        Returns:
            File handle.

        Raises:
            IOError: Cache access error.
        """
        fname = self._note_content_fname(note.guid)
        if not os.path.exists(fname):
            self.logger.debug("fetching content for %s", note.guid)
            content = self.notestore.getNoteContent(self.auth_token, note.guid)
            handle = open(fname, "w")
            handle.write(content)
            handle.close()
        return open(fname)
