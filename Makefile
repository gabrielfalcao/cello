all: unit

unit:
	@nosetests --verbosity=2 -s tests/unit/

functional:
	@nosetests --verbosity=2 -s tests/functional/

integration:
	@nosetests --verbosity=2 -s tests/integration/
