from collections import OrderedDict
import logging
import StringIO
import numpy as np
import os
import unittest

import pandas as pd

from HPOlibConfigSpace.configuration_space import Configuration
import ParamSklearn.classification

import autosklearn.metalearning.optimizers.metalearn_optimizer.metalearner as metalearner

logging.basicConfig()


class MetaLearnerTest(unittest.TestCase):
    _multiprocess_can_split_ = True

    def setUp(self):
        self.cwd = os.getcwd()
        data_dir = os.path.dirname(__file__)
        data_dir = os.path.join(data_dir, 'test_meta_base_data')
        os.chdir(data_dir)

        self.cs = ParamSklearn.classification.ParamSklearnClassifier\
            .get_hyperparameter_search_space()

        self.meta_optimizer = metalearner.MetaLearningOptimizer(
            '16_bac', self.cs, data_dir)

    def tearDown(self):
        os.chdir(self.cwd)

    @unittest.skip("Not yet implemented")
    def test_perform_sequential_optimization(self):
        # TODO: this is only a smoke test!
        def dummy_function(params):
            return params
        ret = self.meta_optimizer.perform_sequential_optimization(
            target_algorithm=dummy_function, evaluation_budget=2)
        self.assertEqual(type(ret), OrderedDict)
        with self.assertRaises(StopIteration):
            self.meta_optimizer.perform_sequential_optimization(dummy_function)

    def test_metalearning_suggest_all(self):
        ret = self.meta_optimizer.metalearning_suggest_all()
        self.assertEqual(2, len(ret))
        self.assertEqual('liblinear_svc', ret[0]['classifier'])
        self.assertEqual('libsvm_svc', ret[1]['classifier'])
        # There is no test for exclude_double_configuration as it's not present
        # in the test data

    def test_metalearning_suggest_all_nan_metafeatures(self):
        self.meta_optimizer.meta_base.metafeatures.loc["16_bac"].iloc[:10] = \
            np.NaN
        ret = self.meta_optimizer.metalearning_suggest_all()
        self.assertEqual(2, len(ret))
        self.assertEqual('liblinear_svc', ret[0]['classifier'])
        self.assertEqual('libsvm_svc', ret[1]['classifier'])

    def test_metalearning_suggest(self):
        ret = self.meta_optimizer.metalearning_suggest([])
        self.assertIsInstance(ret, Configuration)
        self.assertEqual('liblinear_svc', ret['classifier'])
        print ret

        ret2 = self.meta_optimizer.metalearning_suggest([ret])
        self.assertIsInstance(ret2, Configuration)
        self.assertEqual('libsvm_svc', ret2['classifier'])
        print ret2

    def test_learn(self):
        # Test only some special cases which are probably not yet handled
        # like the metafeatures to eliminate and the random forest
        # hyperparameters
        self.meta_optimizer._learn()

    def test_get_metafeatures(self):
        metafeatures, all_other_metafeatures = \
            self.meta_optimizer._get_metafeatures()
        self.assertEqual(type(metafeatures), pd.Series)
        self.assertEqual(type(all_other_metafeatures), pd.DataFrame)
        self.assertEqual(u'16_bac', metafeatures.name)
        self.assertLess(2, metafeatures.shape[0])
        self.meta_optimizer.use_features = ['number_of_classes']
        metafeatures, all_other_metafeatures = \
            self.meta_optimizer._get_metafeatures()
        self.assertGreater(2, metafeatures.shape[0])


    def test_read_task_list(self):
        task_list_file = StringIO.StringIO()
        task_list_file.write('a\nb\nc\nd\n')
        task_list_file.seek(0)
        task_list = self.meta_optimizer.read_task_list(task_list_file)
        self.assertEqual(4, len(task_list))

        task_list_file = StringIO.StringIO()
        task_list_file.write('a\n\nc\nd\n')
        task_list_file.seek(0)
        self.assertRaisesRegexp(ValueError, 'Blank lines in the task list are not supported.',
                                self.meta_optimizer.read_task_list,
                                task_list_file)

    def test_read_experiments_list(self):
        experiments_list_file = StringIO.StringIO()
        experiments_list_file.write('a\nb\n\nc d\n')
        experiments_list_file.seek(0)
        experiments_list = self.meta_optimizer.read_experiments_list(
            experiments_list_file)
        self.assertEqual(4, len(experiments_list))
        self.assertEqual(2, len(experiments_list[3]))

    def test_split_metafeature_array(self):
        metafeatures = self.meta_optimizer.meta_base.metafeatures

        ds_metafeatures, other_metafeatures = self.meta_optimizer. \
            _split_metafeature_array("16_bac", metafeatures)
        self.assertIsInstance(ds_metafeatures, pd.Series)
        self.assertEqual(len(other_metafeatures.index), 122)


if __name__ == "__main__":
    unittest.main()

