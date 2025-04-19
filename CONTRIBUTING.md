# Contributing to PrimisAI Nexus

Thank you for your interest in contributing to Nexus. By participating, you agree to follow our [Code of Conduct](https://github.com/PrimisAI/nexus/blob/main/CODE_OF_CONDUCT.md) and these contribution guidelines.

## 1. Reporting Bugs & Suggesting Enhancements

### Reporting Bugs
- Search existing issues for similar reports.
- If none exist, open a new issue and fill out our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

### Suggesting Enhancements
- Open an issue to discuss your idea before starting work.
- Label it as an "enhancement" and link to any related discussions.

## 2. Developing Locally

1. **Fork & Clone**
    ```bash
    git clone https://github.com/<your-username>/nexus.git
    cd nexus

2. **Create a Virtual Environment (Python 3.10+)**
    ```bash
    python3.10 -m venv venv
    source venv/bin/activate

3. **Install Dependencies**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .

4. **Run Tests & Linting**
    ```bash
    pytest
    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

We enforce PEP8 style and complexity rules via Flake8 in CI.

## 3. Coding Style

- Language: Python 3.10+
- Style Guide: Follow [PEP 8](https://peps.python.org/pep-0008/).
- Line Length: ≤ 127 characters.
- Linting: Configured in [`.github/workflows/tests.yaml`](https://github.com/PrimisAI/nexus/blob/main/.github/workflows/tests.yaml).
- Optional Formatting: You may use [Black](https://black.readthedocs.io/) locally, but ensure Flake8 passes before submitting.

## 4. Commit Messages & PR Titles

We follow the [Conventional Commits](https://www.conventionalcommits.org/) spec. Prefix your commit messages and PR titles with a type and scope, for example:
- feat(core): add Supervisor.display_agent_graph()
- fix(agent): handle missing system_message
- docs: update README examples
- test: add test for hierarchical structure

Pull request titles are automatically validated by GitHub Actions.

## 5. Pull Request Process
1. Branch Naming
    - Features: `feat/<short-description>`
    - Bug fixes: `fix/<short-description>`
2. Implement & Test
    - Add or update code under `primisai`
    - Add tests in the `test` directory.
3. Verify CI Passes
    - Tests (`pytest`)
    - Lint (`flake8`)
    - Semantic PR title
4. Open a PR
    - Base branch: main
    - Include a descriptive title and link related issues (e.g. closes #123).

## 6. Working with Examples

To add or update examples in the `examples` folder:
- Follow the style and structure of existing scripts.
- Provide clear docstrings or README notes so users can run them easily.

## 7. Continuous Integration & Delivery
- **Tests & Lint** run on every push/PR to main via GitHub Actions.
- **Continuous Delivery** publishes new releases automatically when a semantic version tag is pushed, as defined in `.github/workflows/cd.yaml`.

Thank you for helping make PrimisAI Nexus even better! We appreciate your time and expertise.