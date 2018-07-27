set -e
source activate yyy

flake8 yyy
mypy yyy
black yyy