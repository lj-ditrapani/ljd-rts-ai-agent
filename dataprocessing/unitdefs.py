rootdir = '../ljd'


name2id = {}
id2name = {}
unit_def_ids = []
UNUSED = ('armpincer', 'armkam')


def _load_unit_defs():
    f = open(rootdir + '/unitDefs.txt')
    lines = f.read().splitlines()
    for line in lines:
        data = line.split()
        name = data[1]
        if name in UNUSED:
            continue
        defid = int(data[3])
        name2id[name] = defid
        id2name[defid] = name
        unit_def_ids.append(defid)


_load_unit_defs()
