all: install_deps test

filename=cello-`python -c 'import cello;print cello.version'`.tar.gz

export PYTHONPATH:=  ${PWD}
export CELLO_NO_COLORS:=  true

install_deps:
	@pip install -r requirements.pip

test:
	@nosetests -s --verbosity=2 tests
	@steadymark README.md

clean:
	@printf "Cleaning up files that are already in .gitignore... "
	@for pattern in `cat .gitignore`; do rm -rf $$pattern; find . -name "$$pattern" -exec rm -rf {} \;; done
	@echo "OK!"

release: clean test publish
	@printf "Exporting to $(filename)... "
	@tar czf $(filename) cello setup.py README.md
	@echo "DONE!"

publish:
	@python setup.py sdist register upload
