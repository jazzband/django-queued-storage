.PHONY: test release

test:
	py.test

release:
	python setup.py sdist bdist_wheel register upload -s


