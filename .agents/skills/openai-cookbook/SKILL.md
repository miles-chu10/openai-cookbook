```markdown
# openai-cookbook Development Patterns

> Auto-generated skill from repository analysis

## Overview

The `openai-cookbook` repository is a collection of practical guides, code examples, and demos for working with OpenAI APIs in Python. It is organized to encourage contributions of new examples, multi-file demos, and updates to existing content. The repository emphasizes clarity, modularity, and reproducibility, with a focus on Jupyter notebooks, Python scripts, and supporting assets.

## Coding Conventions

- **File Naming:**  
  Use camelCase for file names.  
  _Example:_  
  ```
  textGenerationExample.py
  imageClassificationDemo.ipynb
  ```

- **Import Style:**  
  Use absolute imports.  
  _Example:_  
  ```python
  import openai
  from examples.utils import helper_function
  ```

- **Export Style:**  
  Use named exports (explicitly define what is exported from a module).  
  _Example:_  
  ```python
  def generate_text(prompt):
      ...
  __all__ = ["generate_text"]
  ```

- **Commit Messages:**  
  Freeform, often with `[codex]` prefix.  
  _Example:_  
  ```
  [codex] Add translation notebook for GPT-4
  ```

- **Directory Structure:**  
  - `examples/`: Main location for notebooks, scripts, and demos.
  - `images/`, `assets/`: Supporting files and data.
  - `registry.yaml`: Registry of all examples/demos.
  - `authors.yaml`: Contributor information.

## Workflows

### Add New Cookbook Example
**Trigger:** When contributing a new example, guide, or cookbook (notebook, markdown, or script).  
**Command:** `/new-cookbook`

1. Create new example files (`.ipynb`, `.md`, `.py`) in an appropriate `examples/` subdirectory.
2. Add any required assets (e.g., images, data) in `images/` or `assets/`.
3. Update `registry.yaml` to register the new example.
4. Optionally update `authors.yaml` if new contributors are involved.

_Example:_
```bash
# Add a notebook
cp my_example.ipynb examples/gpt-4/
# Add an image asset
cp diagram.png images/gpt-4/
# Register in registry.yaml
# (edit registry.yaml and add your entry)
```

---

### Add Multifile Demo or App
**Trigger:** When adding a new, often complex, demo or mini-app with multiple files.  
**Command:** `/new-demo`

1. Create a new subdirectory under `examples/` for your demo/app.
2. Add code files (`.py`, `.js`, `.ts`, `.sh`, etc.).
3. Add supporting files: `README.md`, `requirements.txt` or `package.json`, `.gitignore`, etc.
4. Add assets (e.g., images, screenshots, public files).
5. Add tests in a `tests/` or `test/` subfolder.
6. Update `registry.yaml` to register the new demo/app.
7. Optionally update `authors.yaml`.

_Example:_
```bash
mkdir examples/deployment_manager
touch examples/deployment_manager/main.py
touch examples/deployment_manager/README.md
echo "pytest" > examples/deployment_manager/requirements.txt
```

---

### Update Existing Cookbook or Example
**Trigger:** When improving, correcting, or extending an existing example or guide.  
**Command:** `/update-cookbook`

1. Edit the main example file (`.ipynb`, `.md`, etc.).
2. Update or add related assets (e.g., images).
3. Optionally update `registry.yaml` if metadata changes.

---

### Register or Publish Cookbook
**Trigger:** When publishing, archiving, or updating the status of a cookbook/example.  
**Command:** `/update-registry`

1. Edit `registry.yaml` to add, update, or archive cookbook entries.

_Example:_
```yaml
- name: "Text Generation with GPT-4"
  path: "examples/gpt-4/textGenerationExample.ipynb"
  status: "published"
```

---

### Add Author
**Trigger:** When crediting a new author for a new example or update.  
**Command:** `/add-author`

1. Edit `authors.yaml` to add new author information.

_Example:_
```yaml
- name: "Jane Doe"
  github: "janedoe"
  contributions:
    - "Text Generation Example"
```

---

## Testing Patterns

- **Testing Framework:**  
  Uses `vitest` for JavaScript/TypeScript tests.

- **Test File Pattern:**  
  Test files are named with the `.test.js` suffix and placed alongside or within a `tests/` subdirectory.

_Example:_
```
examples/demo_app/tests/api.test.js
```

## Commands

| Command         | Purpose                                                            |
|-----------------|--------------------------------------------------------------------|
| /new-cookbook   | Add a new example, guide, or cookbook to the repository            |
| /new-demo       | Add a new multi-file demo, app, or SDK example                     |
| /update-cookbook| Update or improve an existing example or guide                     |
| /update-registry| Register, publish, or archive a cookbook/example in registry.yaml  |
| /add-author     | Add a new contributor to authors.yaml                              |
```