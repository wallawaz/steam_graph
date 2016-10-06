#! /bin/bash
echo `date`
home_dir=`pwd`
app_dir="$home_dir/steam_graph"

cd "$app_dir/venv"
source bin/activate

# virtualenv is now active, which means your PATH has been modified.
# Don't try to run python from /usr/bin/python, just run "python" and
# let the PATH figure out which version to run (based on what your
# virtualenv has configured).

cd "$app_dir/steam_app"
python run.py --top-games
python run.py --genres
echo "__done__"
