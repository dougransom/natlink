#powershell to run the tests, then build the python package.
$ErrorActionPreference = "Stop"
pytest .\natlinkcore\test\
flit build --format sdist