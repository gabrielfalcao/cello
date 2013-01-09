all: unit

prepare:
	@rm -f .coverage

unit: prepare
	@nosetests --with-coverage --cover-package=cello --verbosity=2 -s tests/unit/

functional: prepare
	@nosetests --with-coverage --cover-package=cello --verbosity=2 -s tests/functional/

integration: prepare
	@nosetests --verbosity=2 -s tests/integration/
