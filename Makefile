all: install_deps test

filename=cello-`python -c 'import cello;print cello.version'`.tar.gz

export CELLO_NO_COLORS:=  true
localshop="http://localshop.staging.yipit.com:8900/"

install_deps:
	@pip install -r requirements.pip

unit: clean
	@nosetests --with-coverage --stop --cover-package=cello --verbosity=2 -s tests/unit/

integration:
	@nosetests -s --verbosity=2 tests/integration

docs:
	@steadymark README.md

test: unit integration docs

clean:
	@printf "Cleaning up files that are already in .gitignore... "
	@for pattern in `cat .gitignore`; do rm -rf $$pattern; find . -name "$$pattern" -exec rm -rf {} \;; done
	@echo "OK!"
	@rm -f .coverage

release: clean test publish
	@printf "Exporting to $(filename)... "
	@tar czf $(filename) cello setup.py README.md
	@echo "DONE!"

publish:
	@python setup.py register -r localshop
	@python setup.py sdist upload -r localshop
