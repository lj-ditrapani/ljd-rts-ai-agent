#! /usr/bin/env python
# Author:  Lyall Jonathan Di Trapani                                          -

import cPickle, sys, time
import numpy as np
import scipy.spatial.distance as dist
import sklearn.cluster as cluster
from sklearn.decomposition import PCA
from sklearn.lda import LDA
from sklearn.svm import SVC
from sklearn.neighbors import NeighborsClassifier
sys.path.append('..')
import config as c


def cross_validate_on_all_maps(use_econ, t):
    for map_size in c.map_sizes:
        cross_validate(map_size, use_econ, t)


def cross_validate(map_size, use_econ, t):
    data_and_sizes_dict = load_data(map_size, use_econ, t)
    for i in range(c.FOLDS):
        # probably need to join 5 matrices in train_data to one matrix
        data_and_sizes = split_data_on_fold(data_and_sizes_dict, i)
        for f_red in c.f_reductions:
            train_data, test_data = reduce_features(f_red, data_and_sizes)
            for c_type in c.classifier_types:
                name = c.make_name(use_econ, t, map_size, f_red, c_type, i)
                run_experiment(train_data, test_data, c_type, name)


def load_data(map_size, use_econ, t):
    path = c.get_data_path(use_econ, t)
    print 'load data for', path, map_size
    f = c.get_data_file(path, map_size, 'r')
    hash_map = cPickle.load(f)
    f.close()
    return hash_map


def split_data_on_fold(data_and_sizes, i):
    print 'splitting data on fold', i
    data, sizes = data_and_sizes['data'], data_and_sizes['fold_sizes']
    train_data = []
    train_sizes = []
    test_data = []
    test_sizes = []
    for data_for_s, sizes_for_s in zip(data, sizes):
        temp = data_for_s[:i] + data_for_s[i + 1:]
        d = []
        # collaps folds of training samples into single list of samples
        for fold in temp:
            d += fold
        train_data.append(d)
        test_data.append(data_for_s[i])
        train_sizes.append(sum(sizes_for_s[:i] + sizes_for_s[i + 1:]))
        test_sizes.append(sizes_for_s[i])
    return train_data, train_sizes, test_data, test_sizes


def reduce_features(f_red, data_and_sizes):
    train_data, train_sizes, test_data, test_sizes = data_and_sizes
    train_data = [np.array(strat_data) for strat_data in train_data]
    test_data = [np.array(strat_data) for strat_data in test_data]
    print f_red
    if f_red == 'non':
        return train_data, test_data
    X1 = np.vstack(train_data)
    X2 = np.vstack(test_data)
    print 'X1 X2 shape', X1.shape, X2.shape
    if f_red == 'pca':
        pca = PCA(n_components=0.95)
        pca.fit(X1)
        pca_X1 = pca.transform(X1)
        pca_X2 = pca.transform(X2)
        print 'pca X1 X2 shape', pca_X1.shape, pca_X2.shape
        print 'pca train min max', pca_X1.min(), pca_X1.max()
        print 'pca test min max', pca_X2.min(), pca_X2.max()
        pca_train_data = split_stack(pca_X1, train_sizes)
        pca_test_data = split_stack(pca_X2, test_sizes)
        print 'pca len', len(pca_train_data), len(pca_test_data)
        return pca_train_data, pca_test_data
    elif f_red == 'lda':
        targets = make_targets(train_data)
        lda = LDA()
        lda.fit(X1, targets)
        lda_X1 = lda.transform(X1)
        lda_X2 = lda.transform(X2)
        print 'lda X1 X2 shape', lda_X1.shape, lda_X2.shape
        print 'lda train min max', lda_X1.min(), lda_X1.max()
        print 'lda test min max', lda_X2.min(), lda_X2.max()
        lda_train_data = split_stack(lda_X1, train_sizes)
        lda_test_data = split_stack(lda_X2, test_sizes)
        print 'lda len', len(lda_train_data), len(lda_test_data)
        # Nomalize data???
        return lda_train_data, lda_test_data


def make_targets(data):
    '''data is a list of size == number of strategies
    each entry contains the samples for that strategy.  
    Can be training or testing data'''
    sizes = [len(strat_data) for strat_data in data]
    targets = []
    for strat_size, i in zip(sizes, range(len(sizes))):
        targets += [i] * strat_size
    return targets


def split_stack(data, sizes):
    d = []
    for size in sizes:
        X, data = data[:size], data[size:]
        d.append(X)
    return d


def run_experiment(train_data, test_data, c_type, name):
    if c_type == 'svm':
        kmeans_ks, knn_ks = [0], [0]
    else:
        kmeans_ks = c.kmeans_ks
        knn_ks = c.knn_ks
    t_shelf = c.get_times_shelf('c')
    for k_kmeans in kmeans_ks:
        cls = make_classifier(train_data, c_type, k_kmeans)
        save_classifier(cls, name, k_kmeans)
        run_tests(cls, test_data, c_type, name, k_kmeans, knn_ks, t_shelf)
    t_shelf.close()


def make_classifier(data, c_type, k_kmeans=0):
    print 'Making classifier', c_type
    if c_type == 'knn':
        return make_knn_classifier(data, k_kmeans)
    elif c_type == 'svm':
        return make_svm_classifier(data)


def make_knn_classifier(data, k):
    labels = []
    means = []
    for i, strat_data in zip(range(len(c.strategies)), data):
        s = 'clustering for {0} with {1} samples'
        print s.format(c.strategies[i], strat_data.shape)
        k_means = cluster.KMeans(k=k)
        k_means.fit(strat_data)
        means.append(k_means.cluster_centers_)
        labels += [i] * k
    print 'clusters shapes'
    for cs in means:
        print cs.shape,
    means = np.vstack(means)
    print 'all means shape', means.shape
    return means, labels


def make_svm_classifier(data):
    targets = make_targets(data)
    svc = SVC()
    X = np.vstack(data)
    svc.fit(X, targets)
    return svc


def save_classifier(classifier, name, k_kmeans):
    f = c.get_class_file(name, k_kmeans, 'wb')
    cPickle.dump(classifier, f)
    f.close()


def run_tests(classifier, test_data, c_type, name, k_kmeans, knn_ks, t_shelf):
    for k_knn in knn_ks:
        if c_type == 'knn':
            means, labels = classifier
            cls = NeighborsClassifier(n_neighbors=k_knn)
            cls.fit(means, labels)
        elif c_type == 'svm':
            cls = classifier
        # results:  every test sample is labeled by classifier
        X = np.vstack(test_data)
        start = time.time()
        results = cls.predict(X)
        elapsed_time = time.time() - start
        save_time(elapsed_time, len(X), t_shelf, name, k_kmeans, k_knn)
        targets = make_targets(test_data)
        save_results(results, targets, name, k_kmeans, k_knn)
        print_results(results, targets)


def save_time(elapsed_time, count, t_shelf, name, k_kmeans, k_knn):
    key = c.get_time_key(name, k_kmeans, k_knn)
    t_shelf[key] = (elapsed_time, count, elapsed_time / count)


def save_results(results, targets, name, k_kmeans, k_knn):
    f = c.get_results_file(name, k_kmeans, k_knn, 'wb')
    cPickle.dump((results, targets), f)
    f.close()


def print_results(results, targets):
    m = len(c.strategies)
    sids = range(m)
    totals = np.bincount(targets)
    print 'totals', totals, 'sids', sids
    for i, count in zip(sids, totals):
        sr, results = results[:count], results[count:]
        bins, _ = np.histogram(sr, sids + [m])
        right = bins[i]
        acc = (right * 1.0) / count
        print 'Acc for {0:8} {1:6.3f}'.format(c.strategies[i], acc)


if __name__ == '__main__':
    t = 32
    '''
    use_econ = False
    map_size = 'sml'
    cross_validate(map_size, use_econ, t)
    '''
    for use_econ in (True, False):
        cross_validate_on_all_maps(use_econ, t)
