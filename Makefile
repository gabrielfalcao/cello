all: unit

prepare:
	@rm -f .coverage
	@find . -name '*.pyc' -delete

unit: prepare
	@nosetests --with-coverage --cover-package=cello --verbosity=2 -s tests/unit/

functional: prepare
	@nosetests --with-coverage --cover-package=cello --verbosity=2 -s tests/functional/

integration: prepare
	@nosetests --verbosity=2 -s tests/integration/
