# Author:  Lyall Jonathan Di Trapani                                          -
# Configuration info used in classifier and dataprocessing scripts

import shelve

MAX_GAMES = 10
FOLDS = 5
NUM_UNITS = 24
NUM_ECON = 8
NUM_TO_DROP = 32            # number of samples to drop at beginning of game
topdir = '../..'
thesisdir = topdir + '/thesis'
rawdatadir = topdir + '/data/raw'
datadir = topdir + '/data/data'
resultsdir = topdir + '/results'
classdir = topdir + '/classifiers'
diagramsdir = thesisdir + '/diagrams'
acctimedir = diagramsdir + '/acctime'
acctabledir = diagramsdir + '/acctables'
conmatdir = diagramsdir + '/conmats'
speeddir = diagramsdir + '/speed'
strategies = (
    'IR',
    'TR',
    'Blitz',
    'Artil',
    'Bomber',
    'Antiair',
    'Exp',
    'Turtle'
)
map_sizes = ('sml', 'med', 'lrg')
f_reductions = ('non', 'pca', 'lda')
classifier_types = ('knn', 'svm')
kmeans_ks = [7]
knn_ks = [1]
econdict = {True: 'econ', False: 'noec'}
namedict = dict(
    sml='Small', med='Medium', lrg='Large', econ='Econ', noec='No Econ', 
    non='None', pca='PCA', lda='LDA', knn='Knn', svm='SVM'
)


def get_data_path(use_econ, t):
    't is the number of samples dropped for each game'
    return '{0}/data/{1}_{2:02}'.format(topdir, econdict[use_econ], t)


def get_data_file(path, map_size, mode):
    return open('{0}/{1}.pickle'.format(path, map_size), mode)


def make_name(use_econ, t, map_size, f_red, c_type, i):
    fmt = '{0}_{1:02}_{2}_{3}_{4}_{5:02}'
    e = econdict[use_econ]
    return fmt.format(e, t, map_size, f_red, c_type, i)

def get_results_file(name, k_kmeans, k_knn, mode):
    fmt = '{0}/{1}_{2:02}_{3:02}.pickle'
    path = fmt.format(resultsdir, name, k_kmeans, k_knn)
    return open(path, mode)


def get_class_file(name, k_kmeans, mode):
    path = '{0}/{1}_{2:02}.pickle'.format(classdir, name, k_kmeans)
    return open(path, mode)


def get_times_shelf(flag):
    'flag: c for read/write/create and r for read-only existing'
    return shelve.open('{0}/timeshelf.db'.format(resultsdir), flag=flag)


def get_time_key(name, k_kmeans, k_knn):
    return '{0}_{1:02}_{2:02}'.format(name, k_kmeans, k_knn)


def get_acc_shelf(flag):
    'flag: c for read/write/create and r for read-only existing'
    return shelve.open('{0}/accshelf.db'.format(resultsdir), flag=flag)


def get_acc_key(use_econ, f_red, c_type, map_size, i):
    e = econdict[use_econ]
    return '{0}_{1}_{2}_{3}_{4:02}'.format(e, f_red, c_type, map_size, i)


def gen_result_name_combinations():
    for use_econ in (True, False):
        for f_red in f_reductions:
            for c_type in classifier_types:
                yield (use_econ, f_red, c_type)


def write_all(f_name, s):
    f = open(f_name, 'w')
    f.write(s)
    f.close()
