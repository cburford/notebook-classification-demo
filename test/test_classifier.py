import unittest
import classifier
from mock import Mock


class TestTokeniser(unittest.TestCase):

    def setUp(self):
        classifier.svmutil = Mock()
        self.svm = classifier.SvmClassifier.train([({"f1": 1}, "l1"),
                                                   ({"f2": 1}, "l2")],
                                                  "param")

    def test_labelindex(self):
        self.assertEqual(self.svm.labelindex, {"l1": 1, "l2": 2})

    def test_featureindex(self):
        self.assertEqual(self.svm.featureindex, {"f1": 1, "f2": 2})

    def test_problem(self):
        classifier.svmutil.svm_problem.assert_called_with([1, 2],
                                                          [{1: 1}, {2: 1}])

    def test_params(self):
        classifier.svmutil.svm_parameter.assert_called_with("param")

    def test_classify(self):
        classifier.svmutil.svm_predict.return_value = ([2, 1], None, None)
        self.assertEqual(self.svm.classify([]), ["l2", "l1"])


if __name__ == '__main__':
    unittest.main()
