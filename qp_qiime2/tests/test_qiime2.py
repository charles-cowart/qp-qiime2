# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from os import remove, stat
from shutil import rmtree
from tempfile import mkdtemp
from json import dumps
from os.path import exists, isdir, join, realpath, dirname
from biom import load_table

from qiita_client.testing import PluginTestCase

from qiime2 import __version__ as qiime2_version
from qiime2.sdk import PluginManager

from qp_qiime2 import plugin, call_qiime2
from qp_qiime2.qp_qiime2 import (
    ALPHA_DIVERSITY_METRICS_PHYLOGENETIC, ALPHA_DIVERSITY_METRICS,
    BETA_DIVERSITY_METRICS, BETA_DIVERSITY_METRICS_PHYLOGENETIC,
    CORRELATION_METHODS, BETA_GROUP_SIG_METHODS)


class qiime2Tests(PluginTestCase):
    def setUp(self):
        # this will allow us to see the full errors
        self.maxDiff = None

        plugin("https://localhost:21174", 'register', 'ignored')
        self._clean_up_files = []

        self.data = {
            'user': 'demo@microbio.me',
            'command': None,
            'status': 'running',
            'parameters': None}

    def tearDown(self):
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    def test_not_analysis_artifact(self):
        params = {
            'The feature table to be rarefied.': '5',
            'The total frequency that each sample should be rarefied to. '
            'Samples where the sum of frequencies is less than the sampling '
            'depth will be not be included in the resulting table unless '
            'subsampling is performed with replacement. (sampling_depth)': '2',
            'qp-hide-method': 'rarefy',
            'qp-hide-paramThe total frequency that each sample should be '
            'rarefied to. Samples where the sum of frequencies is less than '
            'the sampling depth will be not be included in the resulting '
            'table unless subsampling is performed with '
            'replacement. (sampling_depth)': 'sampling_depth',
            'qp-hide-paramThe feature table to be rarefied.': 'table',
            'qp-hide-plugin': 'feature-table'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Rarefy table'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertFalse(success)
        self.assertEqual(msg, 'Artifact "5" is not an analysis artifact.')

    def test_rarefy(self):
        params = {
            'The feature table to be rarefied.': '8',
            'The total frequency that each sample should be rarefied to. '
            'Samples where the sum of frequencies is less than the sampling '
            'depth will be not be included in the resulting table unless '
            'subsampling is performed with replacement. (sampling_depth)': '2',
            'qp-hide-method': 'rarefy',
            'qp-hide-paramThe total frequency that each sample should be '
            'rarefied to. Samples where the sum of frequencies is less than '
            'the sampling depth will be not be included in the resulting '
            'table unless subsampling is performed with '
            'replacement. (sampling_depth)': 'sampling_depth',
            'qp-hide-paramThe feature table to be rarefied.': 'table',
            'qp-hide-plugin': 'feature-table'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Rarefy table'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertTrue(success)
        self.assertEqual(msg, '')
        obs_fp = join(out_dir, 'rarefy', 'rarefied_table',
                      'feature-table.biom')
        self.assertEqual(ainfo[0].files, [(obs_fp, 'biom')])
        self.assertEqual(ainfo[0].artifact_type, 'BIOM')
        self.assertEqual(ainfo[0].output_name, 'rarefied_table')

        # let's check that the new biom has metadata
        b = load_table(obs_fp)
        # as rarefaction is random, we need to get one of the ids to check
        # for metadata
        obs_id = b.ids(axis='observation')[0]
        obs_metadata = b.metadata(obs_id, axis='observation')
        self.assertEqual(obs_metadata['taxonomy'][0], 'k__Bacteria')

    def test_rarefy_error(self):
        params = {
            'The feature table to be rarefied.': '8',
            'The total frequency that each sample should be rarefied to. '
            'Samples where the sum of frequencies is less than the sampling '
            'depth will be not be included in the resulting table unless '
            'subsampling is performed with replacement. '
            '(sampling_depth)': '200000',
            'qp-hide-method': 'rarefy',
            'qp-hide-paramThe total frequency that each sample should be '
            'rarefied to. Samples where the sum of frequencies is less than '
            'the sampling depth will be not be included in the resulting '
            'table unless subsampling is performed with '
            'replacement. (sampling_depth)': 'sampling_depth',
            'qp-hide-paramThe feature table to be rarefied.': 'table',
            'qp-hide-plugin': 'feature-table'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Rarefy table'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']

        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertFalse(success)
        self.assertIsNone(ainfo)
        self.assertEqual(
            msg, 'Error running: The rarefied table contains no samples or '
            'features. Verify your table is valid and that you provided a '
            'shallow enough sampling depth.')

    def test_beta(self):
        params = {
            'A pseudocount to handle zeros for compositional metrics.  This '
            'is ignored for other metrics. (pseudocount)': '1',
            'The beta diversity metric to be '
            'computed. (metric)': "Rogers-Tanimoto distance",
            'The feature table containing the samples over which beta '
            'diversity should be computed.': '8',
            'qp-hide-method': 'beta',
            'qp-hide-paramThe beta diversity metric to be computed. '
            '(metric)': 'metric',
            'qp-hide-paramThe feature table containing the samples over '
            'which beta diversity should be computed.': 'table',
            'qp-hide-plugin': 'diversity',
            'qp-hide-paramA pseudocount to handle zeros for compositional '
            'metrics.  This is ignored for other metrics. '
            '(pseudocount)': 'pseudocount'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Beta diversity'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        self.assertEqual(ainfo[0].files, [(
            join(out_dir, 'beta', 'distance_matrix', 'distance-matrix.tsv'),
            'plain_text')])
        self.assertEqual(ainfo[0].artifact_type, 'distance_matrix')
        self.assertEqual(ainfo[0].output_name, 'distance_matrix')

    def test_beta_phylogenetic(self):
        params = {
            'In a bifurcating tree, the tips make up about 50% of the nodes '
            'in a tree. By ignoring them, specificity can be traded for '
            'reduced compute time. This has the effect of collapsing the '
            'phylogeny, and is analogous (in concept) to moving from 99% '
            'to 97% OTUs (bypass_tips)': True,
            'Perform variance adjustment based on Chang et al. BMC '
            'Bioinformatics 2011. Weights distances based on the proportion '
            'of the relative abundance represented between the samples at a '
            'given node under evaluation. (variance_adjusted)': True,
            'Phylogenetic tree': join(
                dirname(realpath(__file__)), 'prune_97_gg_13_8.tre'),
            'The beta diversity metric to be computed. '
            '(metric)': 'Unweighted UniFrac',
            'The feature table containing the samples over which beta '
            'diversity should be computed.': '8',
            'The number of workers to use. (n_jobs)': '1',
            'This parameter is only used when the choice of metric is '
            'generalized_unifrac. The value of alpha controls importance of '
            'sample proportions. 1.0 is weighted normalized UniFrac. 0.0 is '
            'close to unweighted UniFrac, but only if the sample proportions '
            'are dichotomized. (alpha)': '',
            'qp-hide-method': 'beta_phylogenetic',
            'qp-hide-paramIn a bifurcating tree, the tips make up about 50% '
            'of the nodes in a tree. By ignoring them, specificity can be '
            'traded for reduced compute time. This has the effect of '
            'collapsing the phylogeny, and is analogous (in concept) to '
            'moving from 99% to 97% OTUs (bypass_tips)': 'bypass_tips',
            'qp-hide-paramPerform variance adjustment based on Chang et al. '
            'BMC Bioinformatics 2011. Weights distances based on the '
            'proportion of the relative abundance represented between the '
            'samples at a given node under evaluation. '
            '(variance_adjusted)': 'variance_adjusted',
            'qp-hide-paramPhylogenetic tree': 'phylogeny',
            'qp-hide-paramThe beta diversity metric to be computed. '
            '(metric)': 'metric',
            'qp-hide-paramThe feature table containing the samples over which '
            'beta diversity should be computed.': 'table',
            'qp-hide-paramThe number of workers to use. (n_jobs)': 'n_jobs',
            'qp-hide-paramThis parameter is only used when the choice of '
            'metric is generalized_unifrac. The value of alpha controls '
            'importance of sample proportions. 1.0 is weighted normalized '
            'UniFrac. 0.0 is close to unweighted UniFrac, but only if the '
            'sample proportions are dichotomized. (alpha)': 'alpha',
            'qp-hide-plugin': 'diversity'
        }
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Beta diversity (phylogenetic)'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        self.assertEqual(ainfo[0].files, [(
            join(out_dir, 'beta_phylogenetic', 'distance_matrix',
                 'distance-matrix.tsv'), 'plain_text')])
        self.assertEqual(ainfo[0].artifact_type, 'distance_matrix')
        self.assertEqual(ainfo[0].output_name, 'distance_matrix')

    def test_alpha_rarefaction(self):
        params = {
            'Feature table to compute rarefaction curves from.': '8',
            'Phylogenetic tree': join(
                dirname(realpath(__file__)), 'prune_97_gg_13_8.tre'),
            'The maximum rarefaction depth. Must be greater than min_depth. '
            '(max_depth)': '1000',
            'The metrics to be measured. By default computes observed_otus, '
            'shannon, and if phylogeny is provided, faith_pd. '
            '(metrics)': "Faith's Phylogenetic Diversity",
            'The minimum rarefaction depth. (min_depth)': u'1',
            'The number of rarefaction depths to include between min_depth '
            'and max_depth. (steps)': '10',
            'The number of rarefied feature tables to compute at each step. '
            '(iterations)': '10',
            'qp-hide-metadata': 'metadata',
            'qp-hide-method': 'alpha_rarefaction',
            'qp-hide-paramFeature table to compute rarefaction curves '
            'from.': 'table',
            'qp-hide-paramPhylogenetic tree': 'phylogeny',
            'qp-hide-paramThe maximum rarefaction depth. Must be greater '
            'than min_depth. (max_depth)': 'max_depth',
            'qp-hide-paramThe metrics to be measured. By default computes '
            'observed_otus, shannon, and if phylogeny is provided, faith_pd. '
            '(metrics)': u'metrics',
            'qp-hide-paramThe minimum rarefaction depth. '
            '(min_depth)': 'min_depth',
            'qp-hide-paramThe number of rarefaction depths to include '
            'between min_depth and max_depth. (steps)': 'steps',
            'qp-hide-paramThe number of rarefied feature tables to compute '
            'at each step. (iterations)': 'iterations',
            'qp-hide-plugin': 'diversity'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Alpha rarefaction curves'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        exp = [(join(out_dir, 'alpha_rarefaction',
               'visualization.qzv'), 'qzv')]
        self.assertEqual(ainfo[0].files, exp)
        self.assertEqual(ainfo[0].artifact_type, 'q2_visualization')

    def test_sample_classifier_saplit_table(self):
        # We care about the command running rather the successful creating an
        # output. Additionally, we don't have enough samples in the test
        # dataset to actually run any classifiers so we'll go for failure
        params = {
            'Evenly stratify training and test data among metadata categories.'
            ' If True, all values in column must match at least two samples. '
            '(stratify)': True,
            'Feature table containing all features that should be used for '
            'target prediction.': '8',
            'Fraction of input samples to exclude from training set and use '
            'for classifier testing. (test_size)': '0.2',
            'How to handle missing samples in metadata. "error" will fail if '
            'missing samples are detected. "ignore" will cause the feature '
            'table and metadata to be filtered, so that only samples found '
            'in both files are retained. (missing_samples)': 'ignore',
            'Metadata column to use': 'taxon_id',
            'Seed used by random number generator. (random_state)': '',
            'qp-hide-method': 'split_table',
            'qp-hide-paramEvenly stratify training and test data among '
            'metadata categories. If True, all values in column must match '
            'at least two samples. (stratify)': 'stratify',
            'qp-hide-paramFeature table containing all features that should '
            'be used for target prediction.': 'table',
            'qp-hide-paramFraction of input samples to exclude from training '
            'set and use for classifier testing. (test_size)': 'test_size',
            'qp-hide-paramHow to handle missing samples in metadata. "error" '
            'will fail if missing samples are detected. "ignore" will cause '
            'the feature table and metadata to be filtered, so that only '
            'samples found in both files are retained. '
            '(missing_samples)': 'missing_samples',
            'qp-hide-paramMetadata column to use': 'qp-hide-metadata-field',
            'qp-hide-paramSeed used by random number generator. '
            '(random_state)': 'random_state',
            'qp-hide-plugin': 'sample-classifier'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Split a feature table into training '
             'and testing sets.'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(
            msg, 'Error running: You have chosen to predict a metadata column '
            'that contains one or more values that match only one sample. For '
            'proper stratification of data into training and test sets, each '
            'class (value) must contain at least two samples. This is a '
            'requirement for classification problems, but stratification can '
            'be disabled for regression by setting stratify=False. '
            'Alternatively, remove all samples that bear a unique class '
            'label for your chosen metadata column. Note that disabling '
            'stratification can negatively impact predictive accuracy for '
            'small data sets.')
        self.assertFalse(success)
        self.assertIsNone(ainfo)

    def test_metadata_field(self):
        # as we don't have a distance matrix, we will process one first
        params = {
            'A pseudocount to handle zeros for compositional metrics.  This '
            'is ignored for other metrics. (pseudocount)': '1',
            'The beta diversity metric to be '
            'computed. (metric)': "Rogers-Tanimoto distance",
            'The feature table containing the samples over which beta '
            'diversity should be computed.': '8',
            'The number of jobs to use for the computation. This works '
            'by breaking down the pairwise matrix into n_jobs even slices '
            'and computing them in parallel. If -1 all CPUs are used. If '
            '1 is given, no parallel computing code is used at all, which '
            'is useful for debugging. For n_jobs below -1, (n_cpus + 1 + '
            'n_jobs) are used. Thus for n_jobs = -2, all CPUs but one are '
            'used. (Description from sklearn.metrics.pairwise_distances) '
            '(n_jobs)': '1',
            'qp-hide-method': 'beta',
            'qp-hide-paramThe beta diversity metric to be computed. '
            '(metric)': 'metric',
            'qp-hide-paramThe feature table containing the samples over '
            'which beta diversity should be computed.': 'table',
            'qp-hide-plugin': 'diversity',
            'qp-hide-paramA pseudocount to handle zeros for compositional '
            'metrics.  This is ignored for other metrics. '
            '(pseudocount)': 'pseudocount',
            'qp-hide-paramThe number of jobs to use for the computation. '
            'This works by breaking down the pairwise matrix into n_jobs even '
            'slices and computing them in parallel. If -1 all CPUs are used. '
            'If 1 is given, no parallel computing code is used at all, which '
            'is useful for debugging. For n_jobs below -1, (n_cpus + 1 + '
            'n_jobs) are used. Thus for n_jobs = -2, all CPUs but one are '
            'used. (Description from '
            'sklearn.metrics.pairwise_distances) (n_jobs)': 'n_jobs'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Beta diversity'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        data = {'filepaths': dumps(ainfo[0].files), 'type': "distance_matrix",
                'name': "Non phylogenetic distance matrix", 'analysis': 1,
                'data_type': '16S'}
        reply = self.qclient.post('/apitest/artifact/', data=data)
        aid = reply['artifact']

        params = {
            'If supplied, IDs that are not found in both distance matrices '
            'will be discarded before applying the Mantel test. Default '
            'behavior is to error on any mismatched IDs. '
            '(intersect_ids)': True,
            'Label for `distance_matrix` in the output '
            'visualization. (label1)': 'Metadata',
            'Label for `metadata_distance_matrix` in the output '
            'visualization. (label2)': 'Distance Matrix',
            'Matrix of distances between pairs of samples.': str(aid),
            'Metadata column to use': '',
            'The correlation test to be applied in the Mantel '
            'test. (method)': 'Pearson',
            'The number of permutations to be run when computing p-values. '
            'Supplying a value of zero will disable permutation testing and '
            'p-values will not be calculated (this results in *much* quicker '
            'execution time if p-values are not desired). '
            '(permutations)': '10',
            'qp-hide-method': 'beta_correlation',
            'qp-hide-paramIf supplied, IDs that are not found in both '
            'distance matrices will be discarded before applying the Mantel '
            'test. Default behavior is to error on any mismatched '
            'IDs. (intersect_ids)': 'intersect_ids',
            'qp-hide-paramLabel for `distance_matrix` in the output '
            'visualization. (label1)': 'label1',
            'qp-hide-paramLabel for `metadata_distance_matrix` in the output '
            'visualization. (label2)': 'label2',
            'qp-hide-paramMatrix of distances between pairs of '
            'samples.': 'distance_matrix',
            'qp-hide-paramMetadata column to use': 'qp-hide-metadata-field',
            'qp-hide-paramThe correlation test to be applied in the '
            'Mantel test. (method)': 'method',
            'qp-hide-paramThe number of permutations to be run when '
            'computing p-values. Supplying a value of zero will disable '
            'permutation testing and p-values will not be calculated '
            '(this results in *much* quicker execution time if p-values '
            'are not desired). (permutations)': 'permutations',
            'qp-hide-plugin': 'diversity'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Beta diversity correlation'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, "Error: You didn't write a metadata field in "
                         "'Metadata column to use'")
        self.assertFalse(success)

    def test_beta_correlation(self):
        # as we don't have a distance matrix, we will process one first
        params = {
            'A pseudocount to handle zeros for compositional metrics.  This '
            'is ignored for other metrics. (pseudocount)': '1',
            'The beta diversity metric to be '
            'computed. (metric)': "Rogers-Tanimoto distance",
            'The feature table containing the samples over which beta '
            'diversity should be computed.': '8',
            'The number of jobs to use for the computation. This works '
            'by breaking down the pairwise matrix into n_jobs even slices '
            'and computing them in parallel. If -1 all CPUs are used. If '
            '1 is given, no parallel computing code is used at all, which '
            'is useful for debugging. For n_jobs below -1, (n_cpus + 1 + '
            'n_jobs) are used. Thus for n_jobs = -2, all CPUs but one are '
            'used. (Description from sklearn.metrics.pairwise_distances) '
            '(n_jobs)': '1',
            'qp-hide-method': 'beta',
            'qp-hide-paramThe beta diversity metric to be computed. '
            '(metric)': 'metric',
            'qp-hide-paramThe feature table containing the samples over '
            'which beta diversity should be computed.': 'table',
            'qp-hide-plugin': 'diversity',
            'qp-hide-paramA pseudocount to handle zeros for compositional '
            'metrics.  This is ignored for other metrics. '
            '(pseudocount)': 'pseudocount',
            'qp-hide-paramThe number of jobs to use for the computation. '
            'This works by breaking down the pairwise matrix into n_jobs even '
            'slices and computing them in parallel. If -1 all CPUs are used. '
            'If 1 is given, no parallel computing code is used at all, which '
            'is useful for debugging. For n_jobs below -1, (n_cpus + 1 + '
            'n_jobs) are used. Thus for n_jobs = -2, all CPUs but one are '
            'used. (Description from '
            'sklearn.metrics.pairwise_distances) (n_jobs)': 'n_jobs'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Beta diversity'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        data = {'filepaths': dumps(ainfo[0].files), 'type': "distance_matrix",
                'name': "Non phylogenetic distance matrix", 'analysis': 1,
                'data_type': '16S'}
        reply = self.qclient.post('/apitest/artifact/', data=data)
        aid = reply['artifact']

        params = {
            'If supplied, IDs that are not found in both distance matrices '
            'will be discarded before applying the Mantel test. Default '
            'behavior is to error on any mismatched IDs. '
            '(intersect_ids)': True,
            'Label for `distance_matrix` in the output '
            'visualization. (label1)': 'Metadata',
            'Label for `metadata_distance_matrix` in the output '
            'visualization. (label2)': 'Distance Matrix',
            'Matrix of distances between pairs of samples.': str(aid),
            'Metadata column to use': 'taxon_id',
            'The correlation test to be applied in the Mantel '
            'test. (method)': 'Pearson',
            'The number of permutations to be run when computing p-values. '
            'Supplying a value of zero will disable permutation testing and '
            'p-values will not be calculated (this results in *much* quicker '
            'execution time if p-values are not desired). '
            '(permutations)': '10',
            'qp-hide-method': 'beta_correlation',
            'qp-hide-paramIf supplied, IDs that are not found in both '
            'distance matrices will be discarded before applying the Mantel '
            'test. Default behavior is to error on any mismatched '
            'IDs. (intersect_ids)': 'intersect_ids',
            'qp-hide-paramLabel for `distance_matrix` in the output '
            'visualization. (label1)': 'label1',
            'qp-hide-paramLabel for `metadata_distance_matrix` in the output '
            'visualization. (label2)': 'label2',
            'qp-hide-paramMatrix of distances between pairs of '
            'samples.': 'distance_matrix',
            'qp-hide-paramMetadata column to use': 'qp-hide-metadata-field',
            'qp-hide-paramThe correlation test to be applied in the '
            'Mantel test. (method)': 'method',
            'qp-hide-paramThe number of permutations to be run when '
            'computing p-values. Supplying a value of zero will disable '
            'permutation testing and p-values will not be calculated '
            '(this results in *much* quicker execution time if p-values '
            'are not desired). (permutations)': 'permutations',
            'qp-hide-plugin': 'diversity'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Beta diversity correlation'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        self.assertEqual(ainfo[0].files, [(
            join(out_dir, 'beta_correlation', 'metadata_distance_matrix',
                 'distance-matrix.tsv'), 'plain_text')])
        self.assertEqual(ainfo[0].artifact_type, 'distance_matrix')
        self.assertEqual(ainfo[0].output_name, 'metadata_distance_matrix')
        exp = [(join(out_dir, 'beta_correlation',
               'mantel_scatter_visualization.qzv'), 'qzv')]
        self.assertEqual(ainfo[1].files, exp)
        self.assertEqual(ainfo[1].artifact_type, 'q2_visualization')

    def test_alpha(self):
        params = {
            'The alpha diversity metric to be computed. '
            '(metric)': "Simpson's index",
            'The feature table containing the samples for which alpha '
            'diversity should be computed.': '8',
            'qp-hide-method': 'alpha',
            'qp-hide-paramThe alpha diversity metric to be '
            'computed. (metric)': 'metric',
            'qp-hide-paramThe feature table containing the samples for '
            'which alpha diversity should be computed.': 'table',
            'qp-hide-plugin': 'diversity'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Alpha diversity'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        exp_fp = join(out_dir, 'alpha', 'alpha_diversity',
                      'alpha-diversity.tsv')
        self.assertEqual(ainfo[0].files, [(exp_fp, 'plain_text')])
        self.assertEqual(ainfo[0].artifact_type, 'alpha_vector')
        self.assertEqual(ainfo[0].output_name, 'alpha_diversity')

        # let's test for file permissions
        obs = oct(stat(exp_fp).st_mode)[-3:]
        self.assertEqual(obs, '664')

    def test_alpha_phylogenetic(self):
        params = {
            'Phylogenetic tree': join(
                dirname(realpath(__file__)), 'prune_97_gg_13_8.tre'),
            'The alpha diversity metric to be '
            'computed. (metric)': "Faith's Phylogenetic Diversity",
            'The feature table containing the samples for which alpha '
            'diversity should be computed.': '8',
            'qp-hide-method': 'alpha_phylogenetic',
            'qp-hide-paramPhylogenetic tree': 'phylogeny',
            'qp-hide-paramThe alpha diversity metric to be '
            'computed. (metric)': 'metric',
            'qp-hide-paramThe feature table containing the samples for '
            'which alpha diversity should be computed.': 'table',
            'qp-hide-plugin': 'diversity'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Alpha diversity (phylogenetic)'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        self.assertEqual(ainfo[0].files, [(
            join(out_dir, 'alpha_phylogenetic', 'alpha_diversity',
                 'alpha-diversity.tsv'), 'plain_text')])
        self.assertEqual(ainfo[0].artifact_type, 'alpha_vector')
        self.assertEqual(ainfo[0].output_name, 'alpha_diversity')

    def test_alpha_correlation(self):
        # as we don't have an alpha vector available, we will calculate
        # one using a non phylogenetic metric
        params = {
            'The alpha diversity metric to be computed. '
            '(metric)': "Simpson's index",
            'The feature table containing the samples for which alpha '
            'diversity should be computed.': '8',
            'qp-hide-method': 'alpha',
            'qp-hide-paramThe alpha diversity metric to be '
            'computed. (metric)': 'metric',
            'qp-hide-paramThe feature table containing the samples for '
            'which alpha diversity should be computed.': 'table',
            'qp-hide-plugin': 'diversity'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Alpha diversity'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        data = {'filepaths': dumps(ainfo[0].files), 'type': "alpha_vector",
                'name': "Non phylogenetic alpha vector", 'analysis': 1,
                'data_type': '16S'}
        reply = self.qclient.post('/apitest/artifact/', data=data)
        aid = reply['artifact']

        params = {
            'The correlation test to be applied. (method)': 'Spearman',
            'Vector of alpha diversity values by sample.': str(aid),
            'qp-hide-metadata': 'metadata',
            'qp-hide-method': 'alpha_correlation',
            'qp-hide-paramThe correlation test to be applied. '
            '(method)': 'method',
            'qp-hide-paramVector of alpha diversity values by '
            'sample.': 'alpha_diversity',
            'qp-hide-plugin': 'diversity'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Alpha diversity correlation'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        self.assertEqual(len(ainfo), 1)
        exp = [
            (join(out_dir, 'alpha_correlation', 'visualization.qzv'), 'qzv')]
        self.assertEqual(ainfo[0].files, exp)
        self.assertEqual(ainfo[0].artifact_type, 'q2_visualization')

    def test_taxa_barplot(self):
        params = {
            'Feature table to visualize at various taxonomic levels.': '8',
            'qp-hide-metadata': 'metadata',
            'qp-hide-method': 'barplot',
            'qp-hide-paramFeature table to visualize at various taxonomic '
            'levels.': 'table',
            'qp-hide-plugin': 'taxa',
            'qp-hide-taxonomy': 'taxonomy'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version,
             'Visualize taxonomy with an interactive bar plot'])
        self.data['parameters'] = dumps(params)
        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        self.assertEqual(len(ainfo), 1)
        exp = [
            (join(out_dir, 'barplot', 'visualization.qzv'), 'qzv')]
        self.assertEqual(ainfo[0].files, exp)
        self.assertEqual(ainfo[0].artifact_type, 'q2_visualization')

    def test_filter_samples(self):
        # let's test a failure
        params = {
            'If true, the samples selected by `metadata` or `where` '
            'parameters will be excluded from the filtered table instead of '
            'being retained. (exclude_ids)': False,
            'SQLite WHERE clause specifying sample metadata criteria that '
            'must be met to be included in the filtered feature table. If '
            'not provided, all samples in `metadata` that are also in the '
            'feature table will be retained. '
            '(where)': '"anonymized_name" = "SKB8"',
            'The feature table from which samples should be filtered.': '8',
            'The maximum number of features that a sample can have to be '
            'retained. If no value is provided this will default to infinity '
            '(i.e., no maximum feature filter will be applied). '
            '(max_features)': '14509',
            'The maximum total frequency that a sample can have to be '
            'retained. If no value is provided this will default to infinity '
            '(i.e., no maximum frequency filter will be applied). '
            '(max_frequency)': '',
            'The minimum number of features that a sample must have to be '
            'retained. (min_features)': '0',
            'The minimum total frequency that a sample must have to be '
            'retained. (min_frequency)': '0',
            'qp-hide-metadata': 'metadata',
            'qp-hide-method': 'filter_samples',
            'qp-hide-paramThe feature table from which samples should be '
            'filtered.': 'table',
            'qp-hide-plugin': 'feature-table',
            'qp-hide-paramIf true, the samples selected by `metadata` or '
            '`where` parameters will be excluded from the filtered table '
            'instead of being retained. (exclude_ids)': 'exclude_ids',
            'qp-hide-paramSQLite WHERE clause specifying sample metadata '
            'criteria that must be met to be included in the filtered '
            'feature table. If not provided, all samples in `metadata` that '
            'are also in the feature table will be retained. (where)': 'where',
            'qp-hide-paramThe maximum number of features that a sample can '
            'have to be retained. If no value is provided this will default '
            'to infinity (i.e., no maximum feature filter will be '
            'applied). (max_features)': 'max_features',
            'qp-hide-paramThe maximum total frequency that a sample can have '
            'to be retained. If no value is provided this will default to '
            'infinity (i.e., no maximum frequency filter will be '
            'applied). (max_frequency)': 'max_frequency',
            'qp-hide-paramThe minimum number of features that a sample must '
            'have to be retained. (min_features)': 'min_features',
            'qp-hide-paramThe minimum total frequency that a sample must '
            'have to be retained. (min_frequency)': 'min_frequency'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Filter samples from table'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        self.assertEqual(ainfo[0].files, [(
            join(out_dir, 'filter_samples', 'filtered_table',
                 'feature-table.biom'), 'biom')])
        self.assertEqual(ainfo[0].artifact_type, 'BIOM')
        self.assertEqual(ainfo[0].output_name, 'filtered_table')

    def test_emperor(self):
        # we don't have a pcoa so we will need to calculate beta, then pcoa,
        # and then finally tests emperor
        params = {
            'A pseudocount to handle zeros for compositional metrics.  This '
            'is ignored for other metrics. (pseudocount)': '1',
            'The beta diversity metric to be '
            'computed. (metric)': "Rogers-Tanimoto distance",
            'The feature table containing the samples over which beta '
            'diversity should be computed.': '8',
            'The number of jobs to use for the computation. This works '
            'by breaking down the pairwise matrix into n_jobs even slices '
            'and computing them in parallel. If -1 all CPUs are used. If '
            '1 is given, no parallel computing code is used at all, which '
            'is useful for debugging. For n_jobs below -1, (n_cpus + 1 + '
            'n_jobs) are used. Thus for n_jobs = -2, all CPUs but one are '
            'used. (Description from sklearn.metrics.pairwise_distances) '
            '(n_jobs)': '1',
            'qp-hide-method': 'beta',
            'qp-hide-paramThe beta diversity metric to be computed. '
            '(metric)': 'metric',
            'qp-hide-paramThe feature table containing the samples over '
            'which beta diversity should be computed.': 'table',
            'qp-hide-plugin': 'diversity',
            'qp-hide-paramA pseudocount to handle zeros for compositional '
            'metrics.  This is ignored for other metrics. '
            '(pseudocount)': 'pseudocount',
            'qp-hide-paramThe number of jobs to use for the computation. '
            'This works by breaking down the pairwise matrix into n_jobs even '
            'slices and computing them in parallel. If -1 all CPUs are used. '
            'If 1 is given, no parallel computing code is used at all, which '
            'is useful for debugging. For n_jobs below -1, (n_cpus + 1 + '
            'n_jobs) are used. Thus for n_jobs = -2, all CPUs but one are '
            'used. (Description from '
            'sklearn.metrics.pairwise_distances) (n_jobs)': 'n_jobs'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Beta diversity'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        data = {'filepaths': dumps(ainfo[0].files), 'type': "distance_matrix",
                'name': "Non phylogenetic distance matrix", 'analysis': 1,
                'data_type': '16S'}
        reply = self.qclient.post('/apitest/artifact/', data=data)
        aid = reply['artifact']

        params = {
            "Dimensions to reduce the distance matrix to. This number "
            "determines how many eigenvectors and eigenvalues are "
            "returned,and influences the choice of algorithm used to compute "
            "them. By default, uses the default eigendecomposition method, "
            "SciPy's eigh, which computes all eigenvectors and eigenvalues "
            "in an exact manner. For very large matrices, this is expected to "
            "be slow. If a value is specified for this parameter, then the "
            "fast, heuristic eigendecomposition algorithm fsvd is used, "
            "which only computes and returns the number of dimensions "
            "specified, but suffers some degree of accuracy loss, the "
            "magnitude of which varies across different datasets. "
            "(number_of_dimensions)": '',
            'The distance matrix on which PCoA should be computed.': str(aid),
            'qp-hide-method': 'pcoa',
            'qp-hide-paramThe distance matrix on which PCoA should be '
            'computed.': 'distance_matrix',
            'qp-hide-plugin': 'diversity'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Principal Coordinate Analysis'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        data = {'filepaths': dumps(ainfo[0].files),
                'type': "ordination_results",
                'name': "PCoA results", 'analysis': 1, 'data_type': '16S'}
        reply = self.qclient.post('/apitest/artifact/', data=data)
        aid = reply['artifact']

        params = {
            'Numeric sample metadata columns that should be included as '
            'axes in the Emperor plot. (custom_axes)': '',
            'The principal coordinates matrix to be plotted.': str(aid),
            'qp-hide-metadata': 'metadata',
            'qp-hide-method': 'plot',
            'qp-hide-paramNumeric sample metadata columns that should be '
            'included as axes in the Emperor plot. '
            '(custom_axes)': 'custom_axes',
            'qp-hide-paramThe principal coordinates matrix to be '
            'plotted.': 'pcoa',
            'qp-hide-plugin': 'emperor'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Visualize and Interact with '
             'Principal Coordinates Analysis Plots'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        self.assertEqual(ainfo[0].files, [(
            join(out_dir, 'plot', 'visualization.qzv'), 'qzv')])
        self.assertEqual(ainfo[0].artifact_type, 'q2_visualization')
        self.assertEqual(ainfo[0].output_name, 'visualization')

    def test_beta_group_significance(self):
        # as we don't have a distance matrix, we will process one first
        params = {
            'A pseudocount to handle zeros for compositional metrics.  This '
            'is ignored for other metrics. (pseudocount)': '1',
            'The beta diversity metric to be '
            'computed. (metric)': "Rogers-Tanimoto distance",
            'The feature table containing the samples over which beta '
            'diversity should be computed.': '8',
            'The number of jobs to use for the computation. This works '
            'by breaking down the pairwise matrix into n_jobs even slices '
            'and computing them in parallel. If -1 all CPUs are used. If '
            '1 is given, no parallel computing code is used at all, which '
            'is useful for debugging. For n_jobs below -1, (n_cpus + 1 + '
            'n_jobs) are used. Thus for n_jobs = -2, all CPUs but one are '
            'used. (Description from sklearn.metrics.pairwise_distances) '
            '(n_jobs)': '1',
            'qp-hide-method': 'beta',
            'qp-hide-paramThe beta diversity metric to be computed. '
            '(metric)': 'metric',
            'qp-hide-paramThe feature table containing the samples over '
            'which beta diversity should be computed.': 'table',
            'qp-hide-plugin': 'diversity',
            'qp-hide-paramA pseudocount to handle zeros for compositional '
            'metrics.  This is ignored for other metrics. '
            '(pseudocount)': 'pseudocount',
            'qp-hide-paramThe number of jobs to use for the computation. '
            'This works by breaking down the pairwise matrix into n_jobs even '
            'slices and computing them in parallel. If -1 all CPUs are used. '
            'If 1 is given, no parallel computing code is used at all, which '
            'is useful for debugging. For n_jobs below -1, (n_cpus + 1 + '
            'n_jobs) are used. Thus for n_jobs = -2, all CPUs but one are '
            'used. (Description from '
            'sklearn.metrics.pairwise_distances) (n_jobs)': 'n_jobs'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Beta diversity'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        data = {'filepaths': dumps(ainfo[0].files), 'type': "distance_matrix",
                'name': "Non phylogenetic distance matrix", 'analysis': 1,
                'data_type': '16S'}
        reply = self.qclient.post('/apitest/artifact/', data=data)
        aid = reply['artifact']

        params = {
            'Matrix of distances between pairs of samples.': str(aid),
            'Perform pairwise tests between all pairs of groups in addition '
            'to the test across all groups. This can be very slow if there '
            'are a lot of groups in the metadata column. (pairwise)': True,
            'The group significance test to be applied. (method)': 'PERMANOVA',
            'The number of permutations to be run when computing '
            'p-values. (permutations)': '10',
            'Metadata column to use': 'description_duplicate',
            'qp-hide-paramMetadata column to use': 'qp-hide-metadata-field',
            'qp-hide-method': 'beta_group_significance',
            'qp-hide-paramMatrix of distances between pairs of '
            'samples.': 'distance_matrix',
            'qp-hide-plugin': 'diversity',
            'qp-hide-paramPerform pairwise tests between all pairs of groups '
            'in addition to the test across all groups. This can be very slow '
            'if there are a lot of groups in the metadata column. '
            '(pairwise)': 'pairwise',
            'qp-hide-paramThe group significance test to be '
            'applied. (method)': 'method',
            'qp-hide-paramThe number of permutations to be run when '
            'computing p-values. (permutations)': 'permutations'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Beta diversity group significance'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertFalse(success)
        self.assertEqual(
            msg, "Error running: All values in the grouping vector are "
            "unique. This method cannot operate on a grouping vector with "
            "only unique values (e.g., there are no 'within' distances "
            "because each group of objects contains only a single object).")

    def test_filter_features(self):
        params = {
            'If true, the features selected by `metadata` or `where` '
            'parameters will be excluded from the filtered table instead of '
            'being retained. (exclude_ids)': False,
            'SQLite WHERE clause specifying feature metadata criteria that '
            'must be met to be included in the filtered feature table. If '
            'not provided, all features in `metadata` that are also in the '
            'feature table will be retained. (where)': '',
            'The feature table from which features should be filtered.': '8',
            'The maximum number of samples that a feature can be observed in '
            'to be retained. If no value is provided this will default to '
            'infinity (i.e., no maximum sample filter will be applied). '
            '(max_samples)': '',
            'The maximum total frequency that a feature can have to be '
            'retained. If no value is provided this will default to infinity '
            '(i.e., no maximum frequency filter will be applied). '
            '(max_frequency)': '',
            'The minimum number of samples that a feature must be observed '
            'in to be retained. (min_samples)': '2',
            'The minimum total frequency that a feature must have to be '
            'retained. (min_frequency)': '0',
            'qp-hide-metadata': 'metadata',
            'qp-hide-method': 'filter_features',
            'qp-hide-paramIf true, the features selected by `metadata` or '
            '`where` parameters will be excluded from the filtered table '
            'instead of being retained. (exclude_ids)': 'exclude_ids',
            'qp-hide-paramSQLite WHERE clause specifying feature metadata '
            'criteria that must be met to be included in the filtered '
            'feature table. If not provided, all features in `metadata` '
            'that are also in the feature table will be retained. '
            '(where)': 'where',
            'qp-hide-paramThe feature table from which features should be '
            'filtered.': 'table',
            'qp-hide-paramThe maximum number of samples that a feature can '
            'be observed in to be retained. If no value is provided this will '
            'default to infinity (i.e., no maximum sample filter will be '
            'applied). (max_samples)': 'max_samples',
            'qp-hide-paramThe maximum total frequency that a feature can '
            'have to be retained. If no value is provided this will default '
            'to infinity (i.e., no maximum frequency filter will be applied). '
            '(max_frequency)': 'max_frequency',
            'qp-hide-paramThe minimum number of samples that a feature must '
            'be observed in to be retained. (min_samples)': 'min_samples',
            'qp-hide-paramThe minimum total frequency that a feature must '
            'have to be retained. (min_frequency)': 'min_frequency',
            'qp-hide-plugin': 'feature-table'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Filter features from table'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(msg, '')
        self.assertTrue(success)
        self.assertEqual(ainfo[0].files, [(
            join(out_dir, 'filter_features', 'filtered_table',
                 'feature-table.biom'), 'biom')])
        self.assertEqual(ainfo[0].artifact_type, 'BIOM')
        self.assertEqual(ainfo[0].output_name, 'filtered_table')

    def test_filter_features_failure(self):
        params = {
            'If true, the features selected by `metadata` or `where` '
            'parameters will be excluded from the filtered table instead of '
            'being retained. (exclude_ids)': False,
            'SQLite WHERE clause specifying feature metadata criteria that '
            'must be met to be included in the filtered feature table. If '
            'not provided, all features in `metadata` that are also in the '
            'feature table will be retained. (where)': '',
            'The feature table from which features should be filtered.': '8',
            'The maximum number of samples that a feature can be observed in '
            'to be retained. If no value is provided this will default to '
            'infinity (i.e., no maximum sample filter will be applied). '
            '(max_samples)': '',
            'The maximum total frequency that a feature can have to be '
            'retained. If no value is provided this will default to infinity '
            '(i.e., no maximum frequency filter will be applied). '
            '(max_frequency)': '',
            'The minimum number of samples that a feature must be observed '
            'in to be retained. (min_samples)': '100000000',
            'The minimum total frequency that a feature must have to be '
            'retained. (min_frequency)': '0',
            'qp-hide-metadata': 'metadata',
            'qp-hide-method': 'filter_features',
            'qp-hide-paramIf true, the features selected by `metadata` or '
            '`where` parameters will be excluded from the filtered table '
            'instead of being retained. (exclude_ids)': 'exclude_ids',
            'qp-hide-paramSQLite WHERE clause specifying feature metadata '
            'criteria that must be met to be included in the filtered '
            'feature table. If not provided, all features in `metadata` '
            'that are also in the feature table will be retained. '
            '(where)': 'where',
            'qp-hide-paramThe feature table from which features should be '
            'filtered.': 'table',
            'qp-hide-paramThe maximum number of samples that a feature can '
            'be observed in to be retained. If no value is provided this will '
            'default to infinity (i.e., no maximum sample filter will be '
            'applied). (max_samples)': 'max_samples',
            'qp-hide-paramThe maximum total frequency that a feature can '
            'have to be retained. If no value is provided this will default '
            'to infinity (i.e., no maximum frequency filter will be applied). '
            '(max_frequency)': 'max_frequency',
            'qp-hide-paramThe minimum number of samples that a feature must '
            'be observed in to be retained. (min_samples)': 'min_samples',
            'qp-hide-paramThe minimum total frequency that a feature must '
            'have to be retained. (min_frequency)': 'min_frequency',
            'qp-hide-plugin': 'feature-table'}
        self.data['command'] = dumps(
            ['qiime2', qiime2_version, 'Filter features from table'])
        self.data['parameters'] = dumps(params)

        jid = self.qclient.post(
            '/apitest/processing_job/', data=self.data)['job']
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)

        success, ainfo, msg = call_qiime2(self.qclient, jid, params, out_dir)
        self.assertEqual(
            msg, 'The resulting table is empty, please review your parameters')
        self.assertFalse(success)

    def test_metrics(self):
        pm = PluginManager()
        actions = pm.plugins['diversity'].actions

        # Test alpha diversity metrics
        q2_metrics = actions['alpha'].signature.parameters[
            'metric'].qiime_type.predicate.choices
        qp_metrics = set(ALPHA_DIVERSITY_METRICS.values())
        self.assertEqual(q2_metrics, qp_metrics)

        # Test beta diversity metrics
        q2_metrics = actions['beta'].signature.parameters[
            'metric'].qiime_type.predicate.choices
        qp_metrics = set(BETA_DIVERSITY_METRICS.values())
        self.assertEqual(q2_metrics, qp_metrics)

        q2_metrics = actions['alpha_phylogenetic'].signature.parameters[
            'metric'].qiime_type.predicate.choices
        qp_metrics = set(ALPHA_DIVERSITY_METRICS_PHYLOGENETIC.values())
        self.assertEqual(q2_metrics, qp_metrics)

        q2_metrics = actions['beta_phylogenetic'].signature.parameters[
            'metric'].qiime_type.predicate.choices
        qp_metrics = set(BETA_DIVERSITY_METRICS_PHYLOGENETIC.values())
        self.assertEqual(q2_metrics, qp_metrics)

        # Alpha correlation methods
        q2_metrics = actions['alpha_correlation'].signature.parameters[
            'method'].qiime_type.predicate.choices
        qp_metrics = set(CORRELATION_METHODS.values())
        self.assertEqual(q2_metrics, qp_metrics)

        # Beta correlation methods
        q2_metrics = actions['beta_correlation'].signature.parameters[
            'method'].qiime_type.predicate.choices
        qp_metrics = set(CORRELATION_METHODS.values())
        self.assertEqual(q2_metrics, qp_metrics)

        # Beta group significance method
        q2_metrics = actions['beta_group_significance'].signature.parameters[
            'method'].qiime_type.predicate.choices
        qp_metrics = set(BETA_GROUP_SIG_METHODS.values())
        self.assertEqual(q2_metrics, qp_metrics)


if __name__ == '__main__':
    main()
