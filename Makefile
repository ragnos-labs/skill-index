.PHONY: check index index-check review-bind validate test

check: index-check validate test

index:
	python3 scripts/render_indexes.py

index-check:
	python3 scripts/render_indexes.py --check

review-bind:
	python3 scripts/update_review_digests.py

validate:
	python3 scripts/validate_repository.py

test:
	python3 -m unittest discover -s tests -p 'test_*.py'
