# GitHub API Integration Test Suite

import pytest

# 模拟测试（不需要真实 API）
pytest tests/test_github.py -v -k "not integration"

# 集成测试（需要 GITHUB_TEST_TOKEN 环境变量）
# pytest tests/test_github.py -v -k "integration"

# 所有测试
# pytest tests/test_github.py -v
