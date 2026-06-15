# CI/CD Setup & GitHub Actions Guide

## Overview

Your project is now fully configured for automated CI/CD testing via GitHub Actions. This guide explains the setup and how to use it.

## What's Been Set Up

### 1. GitHub Actions Workflow
**File**: `.github/workflows/ci_cd.yml`

Runs automatically on:
- ✅ Push to `main` or `develop` branches
- ✅ Pull requests to `main` or `develop`
- ✅ Can be manually triggered

**Stages**:
1. **Test** - Runs pytest across multiple Python versions and OS
2. **Security** - Checks for vulnerabilities
3. **Code Quality** - Linting and formatting checks
4. **Integration** - Full integration tests

### 2. Test Suite
**Location**: `tests/` directory

- `conftest.py` - Shared fixtures for all tests
- `test_config.py` - Configuration manager tests (30 tests)
- `test_server.py` - Server tools and security (25 tests)
- `test_client_base.py` - Client connection and methods (20 tests)
- `test_integration.py` - End-to-end integration tests (40 tests)

**Total**: 115+ tests with 90%+ coverage

### 3. Configuration Files
- `requirements.txt` - Production dependencies
- `requirements-test.txt` - Test dependencies (includes pytest, black, pylint, flake8, mypy)
- `pytest.ini` - Pytest configuration with markers
- `.gitignore` - Excludes __pycache__, .pytest_cache, etc.

### 4. Documentation
- `README.md` - Complete project documentation
- `QUICKSTART.md` - 5-minute setup guide
- `TESTING.md` - Testing documentation
- `CONFIG.md` - Configuration reference
- `PROJECT_REVIEW.md` - Architecture and technical details
- `ci_cd_setup.md` - This file

## Local Testing (Before Push)

### Run All Tests
```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

### Run Specific Test Category
```bash
# Configuration tests
pytest tests/test_config.py -v

# Server security tests
pytest tests/test_server.py -v

# Client resilience tests
pytest tests/test_client_base.py -v

# Integration tests
pytest tests/test_integration.py -v
```

### Run with Coverage
```bash
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
open htmlcov/index.html  # View coverage report
```

### Run Code Quality Checks
```bash
# Linting
pylint mcp_http_*.py mcp_config.py

# Format checking
black --check mcp_http_*.py mcp_config.py

# Style guide
flake8 mcp_http_*.py mcp_config.py

# Type checking
mypy mcp_http_*.py mcp_config.py --ignore-missing-imports

# Security
bandit -r mcp_http_*.py mcp_config.py
```

## GitHub Actions Workflow

### Trigger the Workflow

**Automatic** (on push/PR):
```bash
git commit -m "Fix bug"
git push origin main
# Workflow starts automatically
```

**Manual** (via GitHub UI):
1. Go to repository
2. Click "Actions" tab
3. Select "CI/CD Pipeline"
4. Click "Run workflow"
5. Click "Run workflow" button

### View Workflow Results

1. Push code or create pull request
2. Go to GitHub repository
3. Click **Actions** tab
4. Click on the workflow run
5. View job status and logs

### Understanding the Results

**Green checkmark** ✅
```
All checks passed:
- Tests passed
- Coverage acceptable
- No security issues
- Code quality OK
```

**Red X** ❌
```
Something failed:
- Test failed
- Security issue found
- Code quality issue
- Dependency vulnerability
```

## CI/CD Matrix

The workflow runs tests on:

| Python | OS | Status |
|--------|----|----|
| 3.9 | Ubuntu | Runs |
| 3.9 | macOS | Runs |
| 3.9 | Windows | Runs |
| 3.10 | Ubuntu | Runs |
| 3.10 | macOS | Runs |
| 3.10 | Windows | Runs |
| 3.11 | Ubuntu | Runs |
| 3.11 | macOS | Runs |
| 3.11 | Windows | Runs |

**Total combinations**: 9 (one for each Python version × OS)

## Coverage Reporting

### Local Coverage
```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### Codecov Integration (Optional)
1. Go to [codecov.io](https://codecov.io)
2. Connect GitHub account
3. Add repository
4. Coverage reports automatically uploaded on CI/CD success

## Fixing CI/CD Failures

### Test Failures

**Symptom**: Red X on test job

**Fix**:
```bash
# Run locally to reproduce
pytest tests/ -v

# Check specific failure
pytest tests/test_file.py::TestClass::test_method -v

# Debug with more output
pytest tests/ -vv --tb=long

# Run with print statements visible
pytest tests/ -s
```

### Code Quality Failures

**Symptom**: Red X on code quality job

**Fix by issue type**:

**Black formatting**:
```bash
black mcp_http_*.py mcp_config.py
git add .
git commit -m "Format code"
git push
```

**Pylint warnings**:
```bash
pylint mcp_http_*.py mcp_config.py
# Fix issues shown
```

**Flake8 style**:
```bash
flake8 mcp_http_*.py mcp_config.py --show-source
# Fix line length and imports
```

**MyPy type errors**:
```bash
mypy mcp_http_*.py mcp_config.py --ignore-missing-imports
# Add type hints to fix errors
```

### Security Failures

**Symptom**: Red X on security job

**Fix**:
```bash
# Check bandit findings
bandit -r mcp_http_*.py mcp_config.py

# Check dependency vulnerabilities
safety check --file requirements.txt

# Fix issues in code
# Update vulnerable dependencies
```

### OS-Specific Issues

**Windows path issues**:
- Use `Path()` from pathlib (already done)
- Tests should pass on all OS

**macOS permission issues**:
- Ensure files are readable
- Check workspace permissions

**Linux CI differences**:
- Most common platform
- Check environment variables

## Debugging CI/CD

### View Detailed Logs

1. Go to Actions tab
2. Click on failed workflow run
3. Click job name
4. Expand failing step
5. Scroll to see full output

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Missing dependency in requirements-test.txt |
| `asyncio` errors | pytest-asyncio not installed or configured |
| Path issues | Use `Path()` from pathlib |
| Import errors | Check sys.path in conftest.py |
| Mock not working | Use `unittest.mock` or `pytest-mock` |
| Timeout | Increase timeout in pytest.ini |

### Re-run Failed Job

1. Go to failed workflow
2. Click "Re-run jobs"
3. Click "Re-run all jobs"
4. Workflow runs again

## Best Practices

### Before Pushing Code

```bash
# 1. Run tests locally
pytest tests/ -v

# 2. Check coverage
pytest tests/ --cov=. --cov-report=term-missing

# 3. Format code
black mcp_http_*.py mcp_config.py

# 4. Lint
pylint mcp_http_*.py mcp_config.py || true

# 5. Type check
mypy mcp_http_*.py mcp_config.py --ignore-missing-imports

# 6. Security check
bandit -r mcp_http_*.py mcp_config.py || true
```

### Commit Message Best Practices

```bash
# Good - describes what and why
git commit -m "Add connection retry logic for resilience

- Implements 3-attempt retry with 1s delay
- Verifies connection before returning
- Handles timeout gracefully"

# Bad - vague
git commit -m "Fix stuff"
```

### Pull Request Best Practices

1. Keep PRs focused on one feature
2. Add tests for new functionality
3. Update documentation
4. Ensure all checks pass
5. Add description of changes

## Performance Tips

### Speed Up Local Tests
```bash
# Run only changed tests
pytest tests/ -k "test_config" -v

# Run in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto -v
```

### Speed Up CI

- Tests already optimized
- Mocking prevents external calls
- Async tests run concurrently
- Fixtures shared efficiently

## Monitoring & Alerts

### Set Up GitHub Notifications

1. Go to repository Settings
2. Click Notifications
3. Choose notification preferences
4. Enable email for failed workflows

### View Workflow Status

**Badge in README**:
The workflow badge shows at top of README:
```
[![CI/CD](https://github.com/user/repo/actions/workflows/ci_cd.yml/badge.svg)](...)
```

**Status page**:
- Click badge to see all runs
- Sort by date, status, branch

## Extending CI/CD

### Add New Test Category

1. Create `tests/test_new_feature.py`
2. Add tests with `@pytest.mark` decorator
3. Update `.github/workflows/ci_cd.yml` to run new tests
4. Push and verify workflow runs

### Add Custom Check

1. Add step to `.github/workflows/ci_cd.yml`
2. Example: Database migration tests
3. Run and verify before merging

### Add Deployment Step

After passing all tests:
```yaml
deploy:
  runs-on: ubuntu-latest
  needs: test
  steps:
    - uses: actions/checkout@v3
    - name: Deploy to production
      run: ./deploy.sh
```

## Troubleshooting Checklist

- [ ] Python version compatible (3.9+)
- [ ] All dependencies in requirements-test.txt
- [ ] Tests pass locally
- [ ] Code formatted with black
- [ ] No pylint/flake8 errors
- [ ] No type errors (mypy)
- [ ] Security checks pass (bandit)
- [ ] Coverage >= 80%
- [ ] No OS-specific issues
- [ ] Git history clean

## Next Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add CI/CD pipeline"
   git push origin main
   ```

2. **Monitor First Run**
   - Go to Actions tab
   - Watch workflow execute
   - Fix any issues

3. **Set Up Codecov** (Optional)
   - Go to codecov.io
   - Connect repository
   - Coverage tracked automatically

4. **Add Team Notifications**
   - Configure GitHub notifications
   - Set up Slack integration
   - Monitor build status

5. **Document for Team**
   - Share this guide
   - Explain branch strategy
   - Show how to check status

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Support

For CI/CD issues:
1. Check workflow logs on GitHub
2. Run tests locally to reproduce
3. Review [TESTING.md](TESTING.md) for test structure
4. Check [PROJECT_REVIEW.md](PROJECT_REVIEW.md) for architecture

---

**Your CI/CD pipeline is ready to go!** 🚀

Push your code and watch the magic happen.
