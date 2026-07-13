---
name: add-new-cookbook-example
description: Workflow command scaffold for add-new-cookbook-example in openai-cookbook.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-new-cookbook-example

Use this workflow when working on **add-new-cookbook-example** in `openai-cookbook`.

## Goal

Adds a new example, guide, or cookbook to the repository, including code, assets, and registration.

## Common Files

- `examples/**/[!tests]**/*.{ipynb,md,py}`
- `images/**/*`
- `registry.yaml`
- `authors.yaml`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create new example files (e.g., .ipynb, .md, .py) in an appropriate subdirectory under examples/
- Add any required assets (e.g., images/, assets/, data/)
- Update registry.yaml to register the new example
- Optionally update authors.yaml if new authors are involved

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.