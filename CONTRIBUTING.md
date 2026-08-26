# Contributing

By participating in this project, you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).

## Setup your machine

`ai-usage-tracking` is a Claude Code plugin written in Python (standard library only).

Prerequisites:

- [Python 3](https://www.python.org/)
- [Claude Code](https://claude.ai/code)

Clone the repository:

```sh
git clone git@github.com:backmarket-oss/ai-usage-tracking.git
cd ai-usage-tracking
```

## Test your change

The plugin script has no external dependencies — you can run it directly:

```sh
python3 plugins/usage-tracking/skills/usage-tracking/scripts/co2-tracker.py
```

If you have Claude Code installed, you can also test the plugin end-to-end by
installing it locally and running `/usage-tracking`.

## Create a commit

Commit messages should follow [Conventional Commits](https://www.conventionalcommits.org):

```
feat: add new equivalence comparison
fix: correct CO2 calculation for cache tokens
docs: update methodology section
```

## Submit a pull request

1. Fork the repository and create a branch from `main`.
2. Make your changes and commit them.
3. Push to your fork and open a pull request against `main`.
4. Make sure the PR description clearly describes the change and references any related issue.
