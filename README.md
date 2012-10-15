Evernote Notebook Classification Demo
=====================================

Introduction
------------

This code demonstrates the process of downloading notes from an Evernote account, dividing the notes into training and test sets, and using an SVM classifier to predict notebook assignments. It has no practical use other than to illustrate the use of the Evernote API, LIBSVM, and an Evernote-specific feature model.

Requirements and Setup
----------------------

I have tested on Mac OS X and Linux. Python 2.7 is required. Other dependencies are:

* [LIBSVM](http://www.csie.ntu.edu.tw/~cjlin/libsvm/). If you follow the standard install process you will need to manually copy the svm.py and svmutil.py files to somewhere Python can see them.
* [lxml](http://lxml.de/index.html) to parse note XML.
* [prettytable](http://code.google.com/p/prettytable/) to output a table of note classifications to the console.
* The [Evernote SDK for Python](https://github.com/evernote/evernote-sdk-python).

You will also need an Evernote account that you are prepared to have the demo connect to. All of the Evernote API calls used are read-only, but nevertheless, I don't recommend a personal account as a test bed. Instead, set up a new account on the [Evernote Sandbox](http://dev.evernote.com/documentation/cloud/chapters/Testing.php) and populate it with some test content.

For my testing I put together [five test notebooks](http://www.burford.co/test_notebooks.tgz) of approximately 50 notes each from public notebooks I found via the web. Because the notes in these notebooks were created over different periods of time by different users, I scrambled the update times to create more of an illusion of a unified account.

Since the web client doesn't have an import function, you will probably want to import the notes by pointing a desktop client at your sandbox account using the instructions on the sandbox page.

Calls to the Evernote API need an authentication token, normally obtained via OAuth. Since this code is not for production use, its easier to rely on a Developer token, as described on the Evernote API [Authentication](http://dev.evernote.com/documentation/cloud/chapters/Authentication.php) page.

File Descriptions
-----------------

* demo.py. The main module. Execute this from the command-line to run the demo. See in-module documentation for details of the feature model.
* tokenizer.py. A regular expression tokeniser.
* encache.py. A syncing, read-only cache of a user's Evernote note content and metadata. See in-module documentation for details of the on-disk format.
* classifier.py. A convenience wrapper around the LIBSVM Python interface.
* test/*. A set of unit tests.

Usage
-----

Usage information:

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

A sample classification run:

	% mkdir data   # create the default data location
	% ./demo.py S=s1:U=2fa52...
	connected
	updating note f270005d-178f-4646-b9cc-e862fe5946b5
	writing to cache
	fetching content for f270005d-178f-4646-b9cc-e862fe5946b5
	using 16128 features
	Accuracy = 100% (5/5) (classification)
	+--------------------------------+------------------+------------------+----------------+
	|              note              |      actual      |    predicted     |    updated     |
	+--------------------------------+------------------+------------------+----------------+
	| Note from 763 Whitlock Ave ... |   workout_log    |   workout_log    | 20121015 10:58 |
	| Evernote Business: Coming t... | evernote_history | evernote_history | 20121015 10:58 |
	| Phil Libin of Evernote, on ... | evernote_history | evernote_history | 20121015 10:58 |
	| Note from 751 Whitlock Ave ... |   workout_log    |   workout_log    | 20121015 10:58 |
	|       Lonely Back Squats       |   workout_log    |   workout_log    | 20121015 11:34 |
	+--------------------------------+------------------+------------------+----------------+

Performance
-----------

Classifier performance should be expected to be strongly correlated with the number of notebooks in the account. A true, user-centric measure could only be derived with access to a large number of Evernote accounts.

The table below shows performance with my constructed test data. For what it's worth, performance on my ten-notebook personal account was similarly good.

<table>
	<tr><th>Training set size</th><th>Accuracy (%)</th></tr>
	<tr><td>25</td><td>82</td></tr>
	<tr><td>50</td><td>86</td></tr>
	<tr><td>100</td><td>92</td></tr>
	<tr><td>200</td><td>95</td></tr>
</table>

Issues
------

The tokenisation regular expression assumes that words are whitespace separated. This breaks down for languages like Chinese and Japanese. The solution would be to incorporate a language identification step and a morphological analyser.

The bag-of-words feature model generates very large feature counts. This is not a problem for classifier performance, because linear kernel SVMs do an excellent job in this scenario, but it could present a CPU/memory load problem in a large-scale system. In such a case it would be necessary to introduce a feature selection step. See these [two](http://jmlr.csail.mit.edu/papers/volume3/forman03a/forman03a_full.pdf) [papers](http://www.hpl.hp.com/techreports/2004/HPL-2004-86.pdf) for a good starting point.

The feature model does not make use of resource contents. A simple addition would be to add bag-of-words features for the results of NoteStore.getResourceSearchText.
