all: unit

unit:
	@nosetests --with-coverage --cover-package=cello --verbosity=2 -s tests/unit/

functional:
	@nosetests --with-coverage --cover-package=cello --verbosity=2 -s tests/functional/

integration:
	@nosetests --verbosity=2 -s tests/integration/
