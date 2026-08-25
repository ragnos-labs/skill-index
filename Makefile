.PHONY: check index index-check release release-verify review-bind validate test

OUTPUT_DIR ?= dist

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

release: check
	@test -n "$(VERSION)" || (echo "VERSION is required (for example, v0.0.10)" >&2; exit 2)
	python3 scripts/build_release.py "$(VERSION)" --output-dir "$(OUTPUT_DIR)"

release-verify:
	@test -n "$(VERSION)" || (echo "VERSION is required (for example, v0.0.10)" >&2; exit 2)
	python3 scripts/verify_release.py \
		"$(OUTPUT_DIR)/skill-index-$(VERSION).tar.gz" \
		--checksums "$(OUTPUT_DIR)/SHA256SUMS" \
		--version "$(VERSION)"
