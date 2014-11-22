rm ~/.spring/demos/*.sdf
rm data/sml/*.db
rm data/med/*.db
rm data/lrg/*.db
rm output/sml/*
rm output/med/*
rm output/lrg/*
rm replays/sml/*.sdf
rm replays/med/*.sdf
rm replays/lrg/*.sdf
time ./test.py | tee experiment.out
