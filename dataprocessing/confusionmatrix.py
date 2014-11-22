#!/usr/bin/env python
'''
Author:     Lyall Jonathan Di Trapani
File:       confusionMatrix.py
Confusion Matrix Class
'''
import numpy as np
import sys
sys.path.append('..')
import config as c


class ConMat:

    def __init__(self, num_classes):
        self.mat = np.zeros((num_classes, num_classes))
        self.num_classes = num_classes

    def add(self, cls, guess):
        self.mat[cls, guess] += 1

    def clear(self):
        n = self.num_classes
        self.mat = np.zeros((n, n))

    def combine(self, conMat):
        self.mat += conMat.mat

    def print_acc_table(self):
        print r'Class & Sample & Hits & Misses & Acc.\\'
        print r'No. & Count & & & \\'
        print r'\hline'
        rows = self.mat.sum(axis=1)
        for cls_num in range(self.num_classes):
            s = r'{0:7} & {1} & {2} & {3} & {4}\\'
            size = int(rows[cls_num])
            hits = int(self.mat[cls_num, cls_num])
            misses = int(size - hits)
            acc = hits * 1.0 / size
            # if using strategy names
            cls_name = c.strategies[cls_num]
            # if using class numbers
            #cls_name = cls_num + 1
            print s.format(cls_name, size, hits, misses, self.fp(acc))
        print 'Overall Accuracy', self.fp(self.get_acc()), '\n'

    def get_acc(self):
        total = self.mat.sum()
        hits = 0
        for cls_num in range(self.num_classes):
            hits += self.mat[cls_num, cls_num]
        return hits * 1.0 / total

    def __str__(self):
        lines = []
        add = lines.append
        mat = self.mat
        num_cls = self.num_classes
        rows = mat.sum(axis=1)
        cols = mat.sum(axis=0)
        hits = mat.diagonal()
        ca = hits / cols
        pa = hits / rows
        tail = r' \\'
        add(r'\begin{tabular}{|r|' + 'r' * num_cls + '|rr|}')
        add(r'\hline')
        add(r'\rowcolor{lgray} & \multicolumn{' + str(num_cls) + 
            r'}{>{\columncolor{lgray}}c|}{Predicted} & & \\')
        line = []
        line.append(r'\rowcolor{lgray}')
        # if using strategy names
        line += ['{0:7}'.format(s) for s in c.strategies]
        # if using class numbers
        #line += ['{0:6}'.format(i) for i in range(1, num_cls + 1)]
        line += ['Samples', 'PA' + tail]
        add(' & '.join(line))
        add(r'\hline')
        for a_cls_num in range(num_cls):
            line = []
            # if using strategy names
            line.append('{0:7}'.format(c.strategies[a_cls_num]))
            # if using class numbers
            #line.append('{0:6}'.format(a_cls_num + 1))
            for p_cls_num in range(num_cls):
                line.append( '{0:5}'.format(int(mat[a_cls_num, p_cls_num])))
            line.append('{0:5}'.format(int(rows[a_cls_num])))
            line.append(self.fp(pa[a_cls_num]) + tail)
            add(' & '.join(line))
        add(r'\hline')
        line = []
        line.append( 'Totals ')
        for p_cls_num in range(num_cls):
            line.append('{0:6}'.format(int(cols[p_cls_num])))
        line += [' ', tail]
        add(' & '.join(line))
        line = []
        line.append('  CA   ')
        for p_cls_num in range(num_cls):
            line.append('{0:6}'.format(self.fp(ca[p_cls_num])))
        line += [' ', self.fp(self.get_acc()) + tail]
        add(' & '.join(line))
        add(r'\hline')
        add(r'\end{tabular}')
        return '\n'.join(lines) + '\n'

    def save(self, f_name):
        f = open(f_name, 'wb')
        f.write(str(self))
        f.close

    def fp(self, f):
        return r'{0:.1f}\%'.format(f*100)


if __name__ == '__main__':
    # Test code
    s = 4
    cm = ConMat(5)
    iters = 16 
    for i in range(iters):
        x = i % s
        cm.add(x,x)
    for i in range(iters-10):
        cls = i % s
        g = (i + 1) % s
        cm.add(cls,g)
    cm.add(4,4)
    print cm
    cm2 = ConMat(5)
    cm2.add(0,4)
    cm2.add(4,4)
    cm.combine(cm2)
    print cm
    cm.print_acc_table()
