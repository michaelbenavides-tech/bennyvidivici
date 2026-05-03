# Contributing

Use feature branches named `feature/<short-name>`, `bugfix/<short-name>`, or `hotfix/<short-name>`.

Commit messages follow Conventional Commits:

- `feat: add evidence PDF export`
- `fix: resolve artifact upload timeout`
- `docs: update API reference`
- `chore: bump dependencies`

Run checks before opening a PR:

```bash
make test
```

Backend style: Black, isort, flake8, mypy.
Frontend style: ESLint and Prettier.

Every PR should include tests for changed behavior.
