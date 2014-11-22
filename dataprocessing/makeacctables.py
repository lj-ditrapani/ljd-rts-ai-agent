#! /usr/bin/env python
# Author:  Lyall Jonathan Di Trapani                                          -

import cPickle, sys, os
import numpy as np
sys.path.append('..')
import config as c
from confusionmatrix import ConMat


def make_acc_tables():
    t = c.NUM_TO_DROP
    acc_db = c.get_acc_shelf('r')
    dir = c.acctabledir
    if not os.path.isdir(dir):
        os.makedirs(dir)
    for use_econ, f_red, c_type in c.gen_result_name_combinations():
        _make_acc_table(use_econ, t, f_red, c_type, dir, acc_db)
    acc_db.close()


def _make_acc_table(use_econ, t, f_red, c_type, dir, acc_db):
    lines = []
    add = lines.append
    tail = r' \\'
    add(r'\begin{tabular}{|r|' + 'r' * c.FOLDS + '|}')
    add(r'\hline')
    add(r'\rowcolor{lgray} Map & \multicolumn{' + str(c.FOLDS) + 
        r'}{>{\columncolor{lgray}}c|}{Iteration} \\')
    line = [r'\rowcolor{lgray} Size']
    line += ['{0:6}'.format(i) for i in range(1, c.FOLDS + 1)]
    add(' & '.join(line) + tail)
    add(r'\hline')
    for map_size in c.map_sizes:
        line = [c.namedict[map_size]]
        for i in range(c.FOLDS):
            key = c.get_acc_key(use_econ, f_red, c_type, map_size, i)
            line.append('{0:.3f}'.format(acc_db[key]))
        add(' & '.join(line) + tail)
    add(r'\hline')
    add(r'\end{tabular}')
    s = '\n'.join(lines) + '\n'
    print use_econ, f_red, c_type
    print s
    fmt = '{0}_{1}_{2}.tex'
    e = c.econdict[use_econ]
    f_name = fmt.format(e, f_red, c_type)
    c.write_all('{0}/{1}'.format(dir, f_name), s)


def make_acc_compare_table():
    # econ noec non pca lda knn svn
    econ_vals = sorted(c.econdict.values())
    keys = tuple(econ_vals) + c.f_reductions + c.classifier_types 
    d = {}
    for k in keys:
        d[k] = []
    acc_db = c.get_acc_shelf('r')
    for use_econ, f_red, c_type in c.gen_result_name_combinations():
        for map_size in c.map_sizes:
            for i in range(c.FOLDS):
                key = c.get_acc_key(use_econ, f_red, c_type, map_size, i)
                acc = acc_db[key]
                d[c.econdict[use_econ]].append(acc)
                d[f_red].append(acc)
                d[c_type].append(acc)
    acc_db.close()
    means = {}
    stddevs = {}
    for k in keys:
        vals = np.array(d[k])
        means[k] = vals.mean()
        stddevs[k] = vals.std()
    lines = []
    add = lines.append
    tail = r' \\'
    add(r'\begin{tabular}{|r|rr|rrr|rr|}')
    add(r'\hline')
    line = [r'\rowcolor{lgray}']
    line += [c.namedict[k] for k in keys]
    add(' & '.join(line) + tail)
    add(r'\hline')
    line = ['Mean']
    line += ['{0:.4f}'.format(means[k]) for k in keys]
    add(' & '.join(line) + tail)
    line = ['Std Dev']
    line += ['{0:.4f}'.format(stddevs[k]) for k in keys]
    add(' & '.join(line) + tail)
    add(r'\hline')
    add(r'\end{tabular}')
    s = '\n'.join(lines) + '\n'
    print s
    c.write_all('{0}/acccomparetable.tex'.format(c.acctabledir), s)


def make_overall_acc_tables():
    means = dict(knn=[], svm=[])
    stddevs = dict(knn=[], svm=[])
    acc_db = c.get_acc_shelf('r')
    for use_econ, f_red, c_type in c.gen_result_name_combinations():
        mean, std = get_acc_stats(use_econ, f_red, c_type, acc_db)
        means[c_type].append(mean)
        stddevs[c_type].append(std)
    acc_db.close()
    _make_overall_acc_table('mean', means)
    _make_overall_acc_table('stdd', stddevs)


def get_acc_stats(use_econ, f_red, c_type, acc_db):
    accs = []
    for map_size in c.map_sizes:
        for i in range(c.FOLDS):
            key = c.get_acc_key(use_econ, f_red, c_type, map_size, i)
            accs.append(acc_db[key])
    M = np.array(accs)
    return M.mean(), M.std()


def _make_overall_acc_table(mode, data):
    lines = []
    add = lines.append
    tail = r' \\'
    add(r'\begin{tabular}{|r|rrr|rrr|}')
    add(r'\hline')
    add(r'\rowcolor{lgray} & \multicolumn{3}{>{\columncolor{lgray}}c|}' \
        r'{Econ} & \multicolumn{3}{>{\columncolor{lgray}}c|}{No Econ} \\')
    add(r'\hline')
    s = ' & None & PCA & LDA'
    add(r'\rowcolor{lgray}' + s * 2 + tail)
    add(r'\hline')
    for name, key in (('Knn', 'knn'), ('SVM', 'svm')):
        line = [name]
        line += ['{0:.3f}'.format(f) for f in data[key]]
        add(' & '.join(line) + tail)
    add(r'\hline')
    add(r'\end{tabular}')
    s = '\n'.join(lines) + '\n'
    print s
    c.write_all('{0}/accoverall{1}.tex'.format(c.acctabledir, mode), s)


if __name__ == '__main__':
    #make_acc_tables()
    make_acc_compare_table()
    #make_overall_acc_tables()
