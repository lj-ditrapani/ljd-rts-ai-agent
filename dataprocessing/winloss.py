#! /usr/bin/env python
# Author:  Lyall Jonathan Di Trapani                                          -

import sys, shelve
sys.path.append('..')
import config as c


def get_status_index(map_size, strat_a, strat_b, game_num):
    result1 = get_result(map_size, strat_a, strat_a, strat_b, game_num)
    result2 = get_result(map_size, strat_b, strat_a, strat_b, game_num)
    if result1 == 'win' and result2 == 'loss':
        return 0
    elif result1 == 'timeup' and result2 == 'timeup':
        return 1
    elif result1 == 'loss' and result2 == 'win':
        return 2
    else:
        fmt = '{0} {1} {2} {3:02}'
        fname = fmt.format(map_size, strat_a, strat_b, game_num)
        print 'Error in results! ' + fname
        print result1, result2
        raise Exception('Error in results! ' + fname)


def get_result(map_size, persp, strat_a, strat_b, game_num):
    fmt = '{0}/{1}/{2}_{3}_{4}_{5:02}.db'
    fname = fmt.format(c.rawdatadir, map_size, persp, strat_a, 
                       strat_b, game_num)
    db = shelve.open(fname)
    result = db['result']
    db.close()
    return result


def get_raw_matrix(map_size):
    matrix = []
    for strat_a in c.strategies:
        row = []
        for strat_b in c.strategies:
            entry = [0, 0, 0]           # wins, ties, losses
            row.append(entry)
            if strat_a == strat_b:
                continue
            for game_num in range(1, c.MAX_GAMES + 1):
                index = get_status_index(map_size, strat_a, strat_b, game_num)
                if not index is None:
                    entry[index] += 1
        matrix.append(row)
    return matrix


def get_upper_triangle_matrix(matrix):
    size = len(c.strategies)
    utm = []
    for a in range(size):
        row = []
        utm.append(row)
        for b in range(size):
            entry = [0, 0, 0]           # wins, ties, losses
            row.append(entry)
            if a < b:
                d = matrix[a][b]
                entry[0] = d[0]
                entry[1] = d[1]
                entry[2] = d[2]
            else:
                d = matrix[a][b]
                e = utm[b][a]
                e[0] += d[2]
                e[1] += d[1]
                e[2] += d[0]
    return utm


def get_win_loss_matrix(utm):
    n = len(c.strategies)
    wlm = []
    for i in range(n):
        wlm.append([0] * n)
    for a in range(n):
        for b in range(n):
            if a >= b:
                continue
            e = utm[a][b]
            v = e[0] - e[2]
            wlm[a][b] = v
            wlm[b][a] = -v
    return wlm


def print_matrix(matrix, map_size):
    print '\n\n' + map_size + '\n'
    print ' ' * 8,
    for strat_a in c.strategies:
        print '{0:11}'.format(strat_a),
    print ''
    row = 0
    for strat_a in c.strategies:
        print '{0:8}'.format(strat_a),
        col = 0
        for strat_b in c.strategies:
            print '{0:11}'.format(matrix[row][col]),
            col += 1
        row += 1
        print ''


def print_matrix3(matrix, map_size):
    print '\n\n' + map_size + '\n'
    print ' ' * 8,
    for strat_a in c.strategies:
        print '{0:11}'.format(strat_a),
    print ''
    row = 0
    for strat_a in c.strategies:
        print '{0:8}'.format(strat_a),
        col = 0
        for strat_b in c.strategies:
            e = matrix[row][col]
            print '{0:02} {1:02} {2:02}  |'.format(e[0], e[1], e[2]),
            col += 1
        row += 1
        print ''


def make_raw_win_loss_table(m, size):
    lines = []
    add = lines.append
    add(r'\begin{tabular}{|r|' + 'rrr|' * len(c.strategies) + '}')
    add(r'\hline')
    header = [r'\multicolumn{3}{c|}{' + s + '}' for s in c.strategies]
    add(r' & {0} \\'.format(' & '.join(header)))
    add(r'\hline')
    add(r' & {0} \\'.format(' & '.join(['W', 'T', 'L'] * len(c.strategies))))
    add(r'\hline')
    for s, l in zip(c.strategies, m):
        strValues = []
        for e in l:
            if e[0] == e[1] == e[2] == 0:
                strValues.append('  &   &   ')
            else:
                fmt = '{0:2} & {1:2} & {2:2}'
                strValues.append(fmt.format(e[0], e[1], e[2]))
        add(r'{0:7} & {1} \\'.format(s, ' & '.join(strValues)))
    add(r'\hline')
    add(r'\end{tabular}')
    f = open('{0}/raw_winloss_{1}.tex'.format(c.thesisdir, size), 'wb')
    txt = '\n'.join(lines) + '\n'
    f.write(txt)
    f.close()


def make_win_loss_table(m, size):
    lines = []
    add = lines.append
    add(r'\begin{tabular}{|r|' + 'r|' * len(c.strategies) + '}')
    add(r'\hline')
    add(r' & {0} \\'.format(' & '.join(c.strategies)))
    add(r'\hline')
    for s, l in zip(c.strategies, m):
        add(r'{0:7} & {1} \\'.format(s, ' & '.join([str(x) for x in l])))
    add(r'\hline')
    add(r'\end{tabular}')
    f = open('{0}/winloss_{1}.tex'.format(c.thesisdir, size), 'wb')
    txt = '\n'.join(lines) + '\n'
    f.write(txt)
    f.close()


def make_win_loss_rows(sml, med, lrg):
    lines = []
    add = lines.append
    half = '|{0}{0}|{0}|{0}|{0}|'.format('p{0.5in}')
    add(r'\begin{tabular}{' + half * 2 + '}')
    add(r'\hline')
    head = ('Strategy A & Strategy B & Wins on Small Map & '
            'Wins on Medium Map & Wins on Large Map')
    add(r'{0} & {0} \\'.format(head))
    add(r'\hline')
    size = len(c.strategies)
    data = []
    for a in range(size):
        for b in range(size):
            if a >= b:
                continue
            se = sml[a][b]
            sv = se[0] - se[2]
            me = med[a][b]
            mv = me[0] - me[2]
            le = lrg[a][b]
            lv = le[0] - le[2]
            vals = '{0:2} & {1:2} & {2:2}'.format(sv, mv, lv)
            data.append(' & '.join((c.strategies[a], c.strategies[b], vals)))
    half = len(data) / 2
    for i in range(half):
        add(r'{0} & {1} \\'.format(data[i], data[i + half]))
    add(r'\hline')
    add(r'\end{tabular}')
    f = open('{0}/winloss_rows.tex'.format(c.thesisdir), 'wb')
    txt = '\n'.join(lines) + '\n'
    f.write(txt)
    f.close()


def make_counter_strategy_table(win_loss_mats):
    n = len(c.strategies)
    lines = []
    add = lines.append
    add(r'\begin{tabular}{|r|l|l|l|}')
    add(r'\hline')
    add(r'         & \multicolumn{3}{c|}{Best Counter-strategies} \\')
    add(r'\hline')
    add(r'Strategy & Small Map & Medium Map & Large Map \\')
    add(r'\hline')
    for i in range(n):
        s = c.strategies[i]
        cs = []
        for j in range(len(c.map_sizes)):
            cs.append(get_counters(win_loss_mats[j][i]))
        add(r'{0} & {1} & {2} & {3} \\'.format(s, cs[0], cs[1], cs[2]))
    add(r'\hline')
    add(r'\end{tabular}')
    f = open('{0}/counter_strategies.tex'.format(c.thesisdir), 'wb')
    txt = '\n'.join(lines) + '\n'
    f.write(txt)
    f.close()


def get_counters(line):
    cs = []
    min_val = 0
    for s, v in zip(c.strategies, line):
        if v < min_val:
            cs = [s]
            min_val = v
        elif v == min_val:
            cs.append(s)
    return ' '.join(cs)


if __name__ == '__main__':
    uppertm = []
    win_loss_mats = []
    for map_size in c.map_sizes:
        raw_mat = get_raw_matrix(map_size)
        print_matrix3(raw_mat, map_size)
        make_raw_win_loss_table(raw_mat, map_size)
        utm = get_upper_triangle_matrix(raw_mat)
        uppertm.append(utm)
        wlm = get_win_loss_matrix(utm)
        make_win_loss_table(wlm, map_size)
        win_loss_mats.append(wlm)
    make_win_loss_rows(uppertm[0], uppertm[1], uppertm[2])
    for mat, map_size in zip(uppertm, c.map_sizes):
        print_matrix3(mat, map_size)
    for mat, map_size in zip(win_loss_mats, c.map_sizes):
        print_matrix(mat, map_size)
    make_counter_strategy_table(win_loss_mats)

