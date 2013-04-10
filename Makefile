.PHONY: test release doc

test:
	flake8 queued_storage --ignore=E501,E127,E128,E124
	coverage run --branch --source=queued_storage `which django-admin.py` test queued_storage
	coverage report --omit=queued_storage/test*

release:
	python setup.py sdist bdist_wheel register upload -s

doc:
	cd docs; make html; cd ..
