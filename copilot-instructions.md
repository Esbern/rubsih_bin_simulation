# Copilot Instructions (Simulated City Workshop)

This repository is a **beginner-friendly workshop template** for learning agent-based programming in Python.

Your primary goals are:
1. **Teachability**: code should be easy to read and modify.
2. **Cleanliness**: prioritize clean, consistent code over micro-optimizations.
3. **Documentation-driven development (DDD)**: features are documented before they are implemented.

## Top priorities

- Prefer **clear code over efficient code** unless performance is explicitly required.
- Use **simple, explicit control flow**; avoid clever tricks.
- Add **docstrings** to public modules/classes/functions.
- Add **inline comments** when the “why” is not obvious.
- Keep functions small and single-purpose.

## Documentation-driven development

Before implementing or changing behavior:

1. Update or create documentation in `docs/` describing:
   - What the feature does
   - How a student should use it
   - Any configuration required (e.g., `config.yaml`, `.env`)
   - A minimal example

2. Only then implement the feature in code.

3. If relevant, add or update a small test in `tests/`.

### PR requirement (always)

When submitting work (or writing a PR description), include this line in the description:

```
Docs updated: yes/no
```

- If **yes**, include which doc(s) you updated (e.g. `docs/mqtt.md`).
- If **no**, include one short sentence explaining why documentation changes were not needed.

Docs to update depending on change:
- `docs/overview.md` for concepts and workshop framing
- `docs/setup.md` for environment/setup changes
- `docs/mqtt.md` for broker/config changes
- `docs/exercises.md` for student tasks and extensions

## Code style guidelines

- Prefer standard library solutions.
- Prefer dataclasses for simple data containers.
- Avoid deep inheritance; prefer composition.
- Avoid heavy abstractions.
- Favor explicit names over short names.

### Docstrings

- Use a short summary line + (optional) a short explanation.
- Include parameter/return notes when it improves understanding.
- Keep docstrings beginner-friendly (define jargon).

### Comments

- Comment **intent and reasoning** (the “why”), not the obvious “what”.
- Add comments when implementing rules/assumptions in simulations.

## Changes and scope

- Make the **smallest change** that satisfies the requirement.
- Do not add extra features, pages, or tooling unless asked.
- Keep the template cohesive and beginner-oriented.

## Safety and secrets

- Never commit secrets.
- Use `.env` (gitignored) for credentials and `config.yaml` for non-secret defaults.

## Verification

- Prefer `python -m pytest` over calling `pytest` directly.
- If you add dependencies, update `pyproject.toml` and the relevant docs in `docs/`.
