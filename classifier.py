import svmutil


class SvmClassifier(object):
    """Convenience wrapper for LIBSVM classification.

    The purpose of this code is to hide the details of the instance
    representation used by LIBSVM using a 'featureset' representation.
    The only reason to use it is if you prefer this over the LIBSVM
    representation.

    A featureset looks like this:

    ({FEATURE: VALUE, FEATURE: VALUE, ...}, LABEL)

    where FEATURE and LABEL represent string feature names and labels
    respectively.

    The LIBSVM representation requires that feature dictionaries and
    lists of labels be passed as separate parameters. It also requires that
    feature names and labels be integers rather than strings.
    """

    def __init__(self, featureindex, labelindex, model):
        """Accept the label index, feature index and trained model.

        This is not designed to be called directly. Use the train method
        instead.

        Args:
            featureindex: Dictionary mapping feature names to integers.
            labelindex: Dictionary mapping labels to integers.
            model: LIBSVM model as returned by svmutils.svm_train.
        """
        self.labelindex = labelindex
        self.featureindex = featureindex
        self.labelindex_rev = dict((v, k) for k, v in labelindex.iteritems())
        self.model = model

    @classmethod
    def featuresets_to_svm(cls, featureindex, labelindex, featuresets):
        """Map featuresets to LIBSVM vector and label representations.

        Args:
            featureindex: Dictionary mapping feature names to integers.
            labelindex: Dictionary mapping labels to integers.
            featuresets: List of featuresets.

        Returns:
            2-tuple of feature vectors and labels (LIBSVM style).
        """
        vectors = []
        labels = []
        for featuredict, label in featuresets:
            vector = dict([(featureindex[ftr], ftrval)
                           for ftr, ftrval in featuredict.items()
                           if ftr in featureindex])
            vectors.append(vector)
            if label in labelindex:
                labels.append(labelindex[label])
            else:
                labels.append(-1)
        return vectors, labels

    def classify(self, featuresets):
        """Classify a list of featuresets.

        Args:
            featuresets: List of featuresets.

        Returns:
            List of labels, one per featureset.
        """
        vectors, labels = self.featuresets_to_svm(self.featureindex,
                                                  self.labelindex,
                                                  featuresets)
        p_label, _, _ = svmutil.svm_predict(labels, vectors,
                                            self.model)
        return [self.labelindex_rev[int(label)] for label in p_label]

    @classmethod
    def train(cls, featuresets, params="-t 0 -q"):
        """Train a classifier using the given featuresets.

        Args:
            featuresets: List of featuresets.
            params: Parameter string to pass to svmutil.svm_parameter.

        Returns:
            SvmClassifier object.
        """
        all_features = set()
        all_labels = set()
        for featuredict, label in featuresets:
            all_features.update(set(featuredict.keys()))
            all_labels.add(label)
        all_labels = sorted(all_labels)
        all_features = sorted(all_features)
        featureindex = dict(zip(all_features, range(1, len(all_features) + 1)))
        labelindex = dict(zip(all_labels, range(1, len(all_labels) + 1)))
        vectors, labels = cls.featuresets_to_svm(featureindex, labelindex,
                                                 featuresets)
        prob = svmutil.svm_problem(labels, vectors)
        param = svmutil.svm_parameter(params)
        model = svmutil.svm_train(prob, param)
        return cls(featureindex, labelindex, model)
