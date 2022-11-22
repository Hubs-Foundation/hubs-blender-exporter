if ! command -v autopep8 &> /dev/null
then
    echo "Error: autopep8 could not be found: https://pypi.org/project/autopep8/"
    exit -1
fi

cd addons
autopep8 --exclude="**/models" --in-place --recursive --max-line-length=120 --experimental .
