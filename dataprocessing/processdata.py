#! /usr/bin/env python
# Author:  Lyall Jonathan Di Trapani                                          -
# Generate econ and noec data sets (drops first t samples)

import cPickle, sys, os
sys.path.append('..')
import config as c


def prepare_data(t):
    # t is the number of samples to drop from beginning of each game
    for use_econ in (True, False):
        print '\n\nUse econ', use_econ
        path = c.get_data_path(use_econ, t)
        if not os.path.isdir(path):
            os.makedirs(path)
        for map_size in c.map_sizes:
            print '\nMap size', map_size
            data = get_data(use_econ, t, map_size)
            f = c.get_data_file(path, map_size, 'w')
            cPickle.dump(data, f)
            f.close()


def get_data(use_econ, t, map_size):
    # t is the number of samples to drop from beginning of each game
    head = '{0}/{1}'.format(c.datadir, map_size)
    all_data = []
    fold_sizes = []
    for s in c.strategies:
        print '\t', s
        f = open('{0}/{1}_norm.pickle'.format(head, s))
        data_for_s = cPickle.load(f)
        data_for_s = drop_first_t_samples(data_for_s, t)
        if not use_econ:
            drop_econ(data_for_s)
        fold_sizes.append([len(fold) for fold in data_for_s])
        print '\t\tfold_sizes', fold_sizes[-1]
        all_data.append(data_for_s)
    return {'data': all_data, 'fold_sizes': fold_sizes}


def drop_econ(d):
    print '\t\tdrop econ'
    for fold in d:
        for x in fold:
            del x[-c.NUM_ECON:]


def drop_first_t_samples(d, t):
    'Deletes first t samples and collapses games'
    print '\t\tdrop first {0} samples per game'.format(t)
    new_d = []
    for fold in d:
        new_fold = []               # list of samples from all games of fold
        new_d.append(new_fold)
        for game in fold:
            del game[:t]
            new_fold += game        # extend fold with samples from game
    return new_d


if __name__ == '__main__':
    prepare_data(32)
