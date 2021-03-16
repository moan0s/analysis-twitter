docformatter --check -r .
black --check .
isort -c .
flake8 .
