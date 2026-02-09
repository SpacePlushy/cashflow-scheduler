# Scripts

Utility scripts for skill validation and packaging.

## Available Scripts

### `validate_skill.py`

Quick validation of skill structure without packaging.

```bash
python3 scripts/validate_skill.py .
```

**Checks:**
- SKILL.md exists with valid YAML frontmatter
- Required fields: `name`, `description`
- Name format (lowercase, alphanumeric, hyphens)
- Description length (20-200 characters)
- Markdown content exists

### `package_skill.py`

Validate and package skill into distributable zip file.

```bash
# Package to current directory
python3 scripts/package_skill.py .

# Package to specific output directory
python3 scripts/package_skill.py . ./dist
```

**Creates:** `<skill-name>.zip` containing all skill files

**Excludes:**
- Extensions: `.zip`, `.pyc`
- Patterns: `__pycache__/`, `.DS_Store`, `.git/`, `.gitignore`, `node_modules/`, `.venv/`, `venv/`

**Note:** Zip files are explicitly excluded to prevent nested zips in the package.

## Usage Examples

**Before committing changes:**
```bash
python3 scripts/validate_skill.py .
```

**For distribution:**
```bash
python3 scripts/package_skill.py . ./dist
# Output: dist/cashflow-scheduler.zip
```

**Check what's in the package:**
```bash
unzip -l dist/cashflow-scheduler.zip
```
