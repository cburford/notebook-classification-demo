Evernote Notebook Classification Demo
=====================================

Introduction
------------

This code demonstrates the process of downloading notes from an Evernote account, training an SVM classifier on some portion of the notes, and using the classifier to predict the correct notebook assignment for the remainder. It has no practical use other than to demonstrate the use of the Evernote API, LIBSVM, and an Evernote-specific feature model.

Requirements and Setup
----------------------

I have tested this on Mac OS X and Linux with Python 2.7. Required modules are:

* [LIBSVM](http://www.csie.ntu.edu.tw/~cjlin/libsvm/). If you follow the standard install process you will need to manually copy the svm.py and svmutil.py files to somewhere Python can see them.
* The [Evernote SDK for Python](https://github.com/evernote/evernote-sdk-python).

You will also need an Evernote account that you are prepared to have the code connect to. All of the Evernote API calls used are read-only, but nevertheless, I don't recommend a personal account as a test bed. Instead, set up a new account on the [Evernote Sandbox](http://dev.evernote.com/documentation/cloud/chapters/Testing.php) and populate it with some test content.

For my testing I put together five notebooks of approximately 50 notes each from public notebooks I found via the web. They are available [here](http://www.burford.co/evernote_demo_notebooks). Since the web client doesn't have an import function, I followed the instructions on the sandbox page for pointing the Windows client at the Sandbox.

Calls to the Evernote API need an authentication token, normally obtained via OAuth. Since this code is not for production use, its easier to rely on a Developer token, as described on the Evernote API [Authentication](http://dev.evernote.com/documentation/cloud/chapters/Authentication.php) page.

Module Breakdown
----------------

* demo.py. The main module. Execute this from the command-line to run the demo. See in-module documentation for details of the feature model.
* encache.py. A syncing, read-only cache of a user's Evernote note content and metadata. See in-module documentation for details of the on-disk format.
* classifier.py. A convenience wrapper around LIBSVM.

Usage
-----

	% ./demo.py -h
	usage: demo.py [-h] [-s S] [-n N] [-d D] [-r] auth_token

	Evernote notebook classification demo.

	positional arguments:
	  auth_token  authentication token

	optional arguments:
	  -h, --help  show this help message and exit
	  -s S        server (default: sandbox.evernote.com)
	  -n N        number of notes to classify (default: 5)
	  -d D        cache directory (default: ./data)
	  -r          shuffles notes so the test set is random
