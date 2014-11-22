#! /usr/bin/env python
# Author:  Lyall Jonathan Di Trapani                                          -

import time, subprocess, os, sys, shutil, cPickle

MAX_GAMES = 10
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
bin_path = '/home/ljd/springDev/bin/spring'
demo_path = '/home/ljd/.spring/demos'
script_path = '/home/ljd/.spring/AI/Skirmish/ljd'


def run_games_for_map(map_size):
    print '\n\n {0} map'.format(map_size)
    start = time.time()
    times = []
    for strat_a in strategies:
        for strat_b in strategies:
            if strat_a == strat_b:
                continue
            for game_num in range(1, MAX_GAMES + 1):
                times.append(run_game(map_size, strat_a, strat_b, game_num))
    f_name = 'output/{0}/times.pickle'.format(map_size)
    f = open(f_name, 'w')
    cPickle.dump(times, f)
    e_time = (time.time() - start) / 60 / 60
    print '\nOverall time for {0}: {1:0.2f} hours'.format(map_size, e_time)


def run_game(map_size, strat_a, strat_b, game_num):
    # Write config file
    f = open('config/config.txt', 'wb')
    lines = [str(game_num), map_size]
    fmt = 'p{0} {1} on'
    lines.append(fmt.format(1, strat_a))
    lines.append(fmt.format(2, strat_b))
    f.write('\n'.join(lines))
    f.close()
    # Make spring command
    script_name = map_size + '.txt'
    name = '{0}_{1}_{2:02}'.format(strat_a, strat_b, game_num)
    print 'executing for', name
    out_name = 'output/{0}/{1}.out'.format(map_size, name)
    fmt = '{0} {1}/{2} > {3} 2>&1'
    cmd = fmt.format(bin_path, script_path, script_name, out_name)
    # execute game
    start = time.time()
    subprocess.call(cmd, shell=True)
    elapsed_time = time.time() - start
    # Save timing info
    msg = 'elapsed time {0}'.format(elapsed_time)
    print msg
    f = open(out_name, 'a')
    f.write(msg)
    f.close()
    # mv/rename replay
    dirs = os.listdir(demo_path)
    if len(dirs) > 1:
        print 'Too many demos in demo dir!'
        sys.exit(1)
    demo_file = os.path.join(demo_path, dirs[0])
    replay_file = 'replays/{0}/{1}.sdf'.format(map_size, name)
    shutil.move(demo_file, replay_file)
    return elapsed_time


if __name__ == '__main__':
    for map_size in map_sizes:
        run_games_for_map(map_size)
