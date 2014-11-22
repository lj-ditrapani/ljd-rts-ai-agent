#! /usr/bin/env python
# Author:  Lyall Jonathan Di Trapani                                          -

import cPickle, sys, os
import numpy as np
import pylab
sys.path.append('..')
import config as c
from confusionmatrix import ConMat


def make_acc_time_graphs():
    t = c.NUM_TO_DROP
    dir = c.acctimedir
    if not os.path.isdir(dir):
        os.makedirs(dir)
    for use_econ, f_red, c_type in c.gen_result_name_combinations():
        data = {}
        for map_size in c.map_sizes:
            data[map_size] = get_accs(use_econ, t, f_red, c_type, map_size)
        e = c.econdict[use_econ]
        f_name = '{0}/{1}_{2}_{3}.pdf'.format(dir, e, f_red, c_type)
        draw_graph(data, f_name)
    print '\n\n'


def get_accs(use_econ, t, f_red, c_type, map_size):
    right = {}
    total = {}
    head = '{0}/{1}'.format(c.datadir, map_size)
    all_sizes = []
    for s in c.strategies:
        sizes_for_s = []
        all_sizes.append(sizes_for_s)
        print '\t', s
        f = open('{0}/{1}_norm.pickle'.format(head, s))
        d = cPickle.load(f)
        for fold in d:
            sizes_for_fold = []
            sizes_for_s.append(sizes_for_fold)
            for game in fold:
                n = len(game) - c.NUM_TO_DROP
                sizes_for_fold.append(n)
    for i in range(c.FOLDS):
        sizes = get_sizes(all_sizes, i)
        name = c.make_name(use_econ, t, map_size, f_red, c_type, i)
        if c_type == 'svm':
            k_kmeans, k_knn = 0, 0
        else:
            k_kmeans = c.kmeans_ks[0]
            k_knn = c.knn_ks[0]
        f = c.get_results_file(name, k_kmeans, k_knn, 'r')
        results, targets = cPickle.load(f)
        f.close()
        update_acc_over_time(total, right, results, targets, sizes)
    print len(right)
    print len(total)
    times = sorted(total.keys())
    accs = [right[t] * 1.0 / total[t] for t in times]
    return times, accs


def get_sizes(all_sizes, i):
    sizes = []
    for sizes_for_s in all_sizes:
        sizes.append(sizes_for_s[i])    # The i_th fold in strategy data
    return sizes


def update_acc_over_time(total, right, results, targets, sizes):
    n1 = sum([sum(X) for X in sizes])
    n2 = len(targets)
    n3 = len(results)
    if not (n1 == n2 == n3):
        raise Exception('num samples mismatch {0} {1} {2}'.format(n1, n2, n3))
    for sizes_for_s in sizes:
        for n in sizes_for_s:
            rs, results = results[:n], results[n:]
            ts, targets = targets[:n], targets[n:]
            for i in range(n):
                time = ((c.NUM_TO_DROP + i + 1) * 5.0) / 60.0  # in minutes
                if not total.has_key(time):
                    total[time] = 0
                    right[time] = 0
                total[time] += 1
                right[time] += int(rs[i] == ts[i])


def draw_graph(data, f_name):
    fig = pylab.figure()
    pylab.xlabel('time (minutes)')
    pylab.ylabel('accuracy')
    pylab.axis([2, 38, 0.5, 1.01])
    for map_size, marker in zip(c.map_sizes, ('r', 'g--', 'b:')):
        times, accs = data[map_size]
        pylab.plot(times, accs, marker, label=c.namedict[map_size] + ' Map')
    pylab.legend(loc='lower right')
    pylab.savefig(f_name, bbox_inches='tight', pad_inches=0.1)

def make_exec_speed_tables():
    means = dict(knn=[], svm=[])
    stddevs = dict(knn=[], svm=[])
    time_db = c.get_times_shelf('r')
    for use_econ, f_red, c_type in c.gen_result_name_combinations():
        mean, std = get_time_stats(use_econ, f_red, c_type, time_db)
        means[c_type].append(mean)
        stddevs[c_type].append(std)
    time_db.close()
    _make_exec_speed_table('mean', means)
    _make_exec_speed_table('stdd', stddevs)


def get_time_stats(use_econ, f_red, c_type, time_db):
    times = []
    for map_size in c.map_sizes:
        for i in range(c.FOLDS):
            name = c.make_name(use_econ, c.NUM_TO_DROP, map_size, 
                             f_red, c_type, i)
            if c_type == 'svm':
                k_kmeans, k_knn = 0, 0
            else:
                k_kmeans = c.kmeans_ks[0]
                k_knn = c.knn_ks[0]
            key = c.get_time_key(name, k_kmeans, k_knn)
            elapsed_time, count, tps = time_db[key]
            times.append(tps)
    M = np.array(times)
    return M.mean(), M.std()


def _make_exec_speed_table(mode, data):
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
        line += ['{0:.2f}'.format(f * 1000000) for f in data[key]]
        add(' & '.join(line) + tail)
    add(r'\hline')
    add(r'\end{tabular}')
    s = '\n'.join(lines) + '\n'
    print s
    c.write_all('{0}/execspeed{1}.tex'.format(c.acctimedir, mode), s)


if __name__ == '__main__':
    make_acc_time_graphs()
    make_exec_speed_tables()
