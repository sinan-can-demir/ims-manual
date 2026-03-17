# -------------------------
# Pytest (fast tests)
# -------------------------
test:
	pytest

# -------------------------
# E2E System Test (Docker)
# -------------------------
test-e2e:
	sh test_scripts/test_sc.sh

# -------------------------
# Full pipeline
# -------------------------
test-all:
	make test
	make test-e2e

# -------------------------
# Cleanup
# -------------------------
test-clean:
	rm -rf .pytest_cache