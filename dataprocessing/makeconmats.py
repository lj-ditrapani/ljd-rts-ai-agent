#! /usr/bin/env python
# Author:  Lyall Jonathan Di Trapani                                          -

import cPickle, sys, os
sys.path.append('..')
import config as c
from confusionmatrix import ConMat


def make_con_mats():
    t = c.NUM_TO_DROP
    acc_db = c.get_acc_shelf('c')
    dir = c.conmatdir
    if not os.path.isdir(dir):
        os.makedirs(dir)
    for use_econ, f_red, c_type in c.gen_result_name_combinations():
        for map_size in c.map_sizes:
            _make_con_mat(use_econ, t, f_red, c_type, map_size, dir, acc_db)
    acc_db.close()


def _make_con_mat(use_econ, t, f_red, c_type, map_size, dir, acc_db):
    cm = ConMat(len(c.strategies))
    for i in range(c.FOLDS):
        temp_cm = ConMat(len(c.strategies))
        name = c.make_name(use_econ, t, map_size, f_red, c_type, i)
        if c_type == 'svm':
            k_kmeans, k_knn = 0, 0
        else:
            k_kmeans = c.kmeans_ks[0]
            k_knn = c.knn_ks[0]
        f = c.get_results_file(name, k_kmeans, k_knn, 'r')
        results, targets = cPickle.load(f)
        f.close()
        for guess, label in zip(results, targets):
            temp_cm.add(label, guess)
        key = c.get_acc_key(use_econ, f_red, c_type, map_size, i)
        acc_db[key] = temp_cm.get_acc()
        cm.combine(temp_cm)
    print use_econ, f_red, c_type, map_size, cm.get_acc()
    fmt = '{0}_{1}_{2}_{3}.tex'
    e = c.econdict[use_econ]
    f_name = fmt.format(e, f_red, c_type, map_size)
    cm.save('{0}/{1}'.format(dir, f_name))


if __name__ == '__main__':
    make_con_mats()
