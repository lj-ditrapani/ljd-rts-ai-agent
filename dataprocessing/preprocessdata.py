#! /usr/bin/env python
# Author:  Lyall Jonathan Di Trapani                                          -
# Create processed data (in data/) Collect data into strategies per map

import cPickle, shelve, sys
sys.path.append('..')
import unitdefs
import config as c


def get_num_samples_per_game():
    print 'Get num samples per game'
    for map_size in c.map_sizes:
        print '\n\n\n\n', '=== new map_size', map_size, '===\n\n'
        get_num_samples_per_game_for_map(map_size)


def get_num_samples_per_game_for_map(map_size):
    m = len(c.strategies)
    min_samples = 10000
    sum_avg = 0
    for s in c.strategies:
        print '\n\nnew strategy', s, '\n'
        sumn = 0
        for o in c.strategies:
            if s == o:
                continue
            for strata, stratb in ((s, o), (o, s)):
                print '{0:8} {1:8}'.format(strata, stratb),
                for i in range(c.MAX_GAMES):
                    data = get_game_data(map_size, s, strata, stratb, i + 1)
                    n = len(data)
                    if n < min_samples:
                        min_samples = n
                    sumn += n
                    print '{0:4}'.format(n),
                print ''
        avg = sumn * 1.0 / (2 * (m - 1) * c.MAX_GAMES)
        print 'avg', avg
        sum_avg += avg
    print '\nAvg for map', sum_avg * 1.0 / m
    print '\n\nMin samples:', min_samples


def rawdata2data():
    for map_size in c.map_sizes:
        print '\n\n\n\n', '=== new map_size', map_size, '===\n\n'
        process_raw_data_for_map(map_size)


def process_raw_data_for_map(map_size):
    games_per_set = c.MAX_GAMES / c.FOLDS
    for s in c.strategies:
        print '\n\nnew strategy', s, '\n'
        data = []
        for f in range(c.FOLDS):
            m = []                          # new matrix for each fold
            data.append(m)
            for o in c.strategies:
                if s == o:
                    continue
                for strata, stratb in ((s, o), (o, s)):
                    for i in range(games_per_set):
                        game_num = f * games_per_set + i
                        xs = get_game_samples(map_size, s, strata,
                                              stratb, game_num + 1)
                        m.append(xs)
            print 'Num samples in m:', sum([len(xs) for xs in m])
        # write to data dir for strat and map
        write_data(map_size, s, data, '')


def get_game_samples(map_size, strat, strata, stratb, game_num):
    data = get_game_data(map_size, strat, strata, stratb, game_num)
    xs = [get_sample(rd) for rd in data]
    if len(xs[0]) != 32:
        raise Exception('Number of features = ' + len(xs[0]))
    return xs


def get_game_data(map_size, strat, strata, stratb, game_num):
    fmt = '{0}/{1}/{2}_{3}_{4}_{5:02}.db'
    fname = fmt.format(c.rawdatadir, map_size, strat, strata, stratb, game_num)
    db = shelve.open(fname)
    data = db['data']
    db.close()
    return data


def get_sample(rd):
    units = rd[1]
    econ = [x for x in rd[2]]
    d = {}
    for defid in unitdefs.unit_def_ids:
        if defid == 43:                 # armcom commander definition ID
            continue
        d[defid] = 0
    for unit in units:
        defid = unit[0]
        if defid == 43:                 # armcom commander definition ID
            continue
        d[defid] += 1
    return [d[defid] for defid in unitdefs.unit_def_ids if defid != 43] + econ


def write_data(map_size, strat, data, prefix):
    fmt = '{0}/{1}/{2}{3}.pickle'
    fname = fmt.format(c.datadir, map_size, strat, prefix)
    f = open(fname, 'w')
    cPickle.dump(data, f)
    f.close()


def get_min_max():
    for map_size in c.map_sizes:
        print '\n\n\n', '=== new map_size', map_size, '===\n\n'
        mins, maxs = get_min_max_for_map(map_size)
        print 'mins', mins
        print 'maxs', maxs
        f = open('{0}/{1}/min_max.pickle'.format(c.datadir, map_size), 'w')
        cPickle.dump([mins, maxs], f)
        f.close()


def get_min_max_for_map(map_size):
    num_features = c.NUM_UNITS + c.NUM_ECON
    mins = [1000.0] * c.NUM_UNITS + [10000.0] * c.NUM_ECON
    maxs = [0.0] * c.NUM_UNITS + [-10000.0] * c.NUM_ECON
    for strat in c.strategies:
        fmt = '{0}/{1}/{2}.pickle'
        fname = fmt.format(c.datadir, map_size, strat)
        f = open(fname)
        data = cPickle.load(f)
        f.close()
        for m in data:
            for xs in m:
                for x in xs:
                    for i in range(num_features):
                        v = float(x[i])
                        if v < mins[i]:
                            mins[i] = v
                        if v > maxs[i]:
                            maxs[i] = v
    return mins, maxs


def normalize_data():
    for map_size in c.map_sizes:
        print '\n\n\n', '=== new map_size', map_size, '===\n\n'
        mins, maxs = load_mins_maxs(map_size)
        normalize_data_for_map(map_size, mins, maxs)


def normalize_data_for_map(map_size, mins, maxs):
    num_features = c.NUM_UNITS + c.NUM_ECON
    MIN = -1.0
    MAX = 1.0
    for strat in c.strategies:
        fmt = '{0}/{1}/{2}.pickle'
        fname = fmt.format(c.datadir, map_size, strat)
        f = open(fname)
        data = cPickle.load(f)
        f.close()
        for m in data:
            for xs in m:
                for x in xs:
                    for i in range(num_features):
                        a = (x[i] * 1.0 - mins[i]) * (MAX - MIN)
                        b = (maxs[i] * 1.0 - mins[i] * 1.0)
                        x[i] = MIN + a / b
        write_data(map_size, strat, data, '_norm')


def load_mins_maxs(map_size):
    f = open('{0}/{1}/min_max.pickle'.format(c.datadir, map_size))
    mins, maxs = cPickle.load(f)
    f.close()
    return mins, maxs
    

if __name__ == '__main__':
    get_num_samples_per_game()
    rawdata2data()
    get_min_max()
    normalize_data()
