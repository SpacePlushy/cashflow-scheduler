#!/usr/bin/env python3
"""Package and validate a Claude skill for distribution.

This script validates skill structure and packages it into a distributable zip file.

Usage:
    python scripts/package_skill.py <path/to/skill>
    python scripts/package_skill.py <path/to/skill> <output-dir>

Example:
    python scripts/package_skill.py . ./dist
    # Creates: dist/cashflow-scheduler.zip
"""

import sys
import re
import zipfile
from pathlib import Path
from typing import List, Tuple, Optional


class ValidationError(Exception):
    """Skill validation failed"""
    pass


def validate_skill(skill_path: Path) -> Tuple[str, str]:
    """Validate skill structure and return (name, description).

    Args:
        skill_path: Path to skill directory

    Returns:
        Tuple of (skill_name, skill_description)

    Raises:
        ValidationError: If validation fails
    """
    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        raise ValidationError(f"Missing required file: SKILL.md")

    # Read SKILL.md
    content = skill_md.read_text()

    # Check for YAML frontmatter
    if not content.startswith('---'):
        raise ValidationError("SKILL.md must start with YAML frontmatter (---)")

    # Extract frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValidationError("SKILL.md has malformed YAML frontmatter")

    frontmatter = parts[1]

    # Extract name
    name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
    if not name_match:
        raise ValidationError("SKILL.md frontmatter missing required field: name")
    name = name_match.group(1).strip()

    # Extract description
    desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
    if not desc_match:
        raise ValidationError("SKILL.md frontmatter missing required field: description")
    description = desc_match.group(1).strip()

    # Validate name format
    if not re.match(r'^[a-z0-9\-]+$', name):
        raise ValidationError(
            f"Skill name '{name}' must be lowercase alphanumeric with hyphens only"
        )

    # Validate description length
    if len(description) < 20:
        raise ValidationError(
            f"Description too short ({len(description)} chars). Must be at least 20 characters."
        )
    if len(description) > 200:
        print(f"⚠️  Warning: Description is long ({len(description)} chars). "
              f"Consider keeping it under 200 characters.")

    # Check markdown content exists
    markdown_content = parts[2].strip()
    if len(markdown_content) < 100:
        raise ValidationError("SKILL.md has insufficient content (< 100 characters)")

    print(f"✅ SKILL.md validated")
    print(f"   Name: {name}")
    print(f"   Description: {description[:60]}...")

    return name, description


def check_optional_resources(skill_path: Path) -> None:
    """Check for optional resource directories and report findings."""
    optional_dirs = ['scripts', 'references', 'assets', 'examples']
    found = []

    for dir_name in optional_dirs:
        dir_path = skill_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            file_count = len(list(dir_path.rglob('*')))
            found.append(f"{dir_name}/ ({file_count} files)")

    if found:
        print(f"✅ Optional resources: {', '.join(found)}")
    else:
        print(f"ℹ️  No optional resource directories (scripts/, references/, assets/, examples/)")


def package_skill(skill_path: Path, output_dir: Optional[Path] = None) -> Path:
    """Package skill into a zip file.

    Args:
        skill_path: Path to skill directory
        output_dir: Optional output directory (defaults to current directory)

    Returns:
        Path to created zip file
    """
    # Validate first
    name, description = validate_skill(skill_path)
    check_optional_resources(skill_path)

    # Determine output path
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir / f"{name}.zip"

    # Create zip file
    print(f"\n📦 Packaging skill...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add all files, excluding common unwanted patterns
        exclude_patterns = {
            '__pycache__',
            '.pyc',
            '.DS_Store',
            '.git',
            '.gitignore',
            'node_modules',
            '.venv',
            'venv',
        }

        exclude_extensions = {'.zip', '.pyc'}

        file_count = 0
        for file_path in skill_path.rglob('*'):
            # Skip directories
            if file_path.is_dir():
                continue

            # Skip files with excluded extensions
            if file_path.suffix.lower() in exclude_extensions:
                continue

            # Skip excluded patterns
            if any(pattern in str(file_path) for pattern in exclude_patterns):
                continue

            # Add to zip with relative path
            arcname = file_path.relative_to(skill_path)
            zf.write(file_path, arcname)
            file_count += 1

    print(f"✅ Packaged {file_count} files into: {zip_path}")
    print(f"   Size: {zip_path.stat().st_size / 1024:.1f} KB")

    return zip_path


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    skill_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    # Validate skill path exists
    if not skill_path.exists():
        print(f"❌ Error: Skill path does not exist: {skill_path}")
        sys.exit(1)

    if not skill_path.is_dir():
        print(f"❌ Error: Skill path is not a directory: {skill_path}")
        sys.exit(1)

    print(f"{'=' * 60}")
    print(f"PACKAGING SKILL: {skill_path.name}")
    print(f"{'=' * 60}\n")

    try:
        zip_path = package_skill(skill_path, output_dir)
        print(f"\n{'=' * 60}")
        print(f"✅ SUCCESS")
        print(f"{'=' * 60}")
        print(f"\nSkill packaged successfully!")
        print(f"Output: {zip_path}")
        print(f"\nTo use this skill:")
        print(f"  1. Copy {zip_path.name} to your skills directory")
        print(f"  2. Unzip: unzip {zip_path.name}")
        print(f"  3. Load in Claude Code")

    except ValidationError as e:
        print(f"\n{'=' * 60}")
        print(f"❌ VALIDATION FAILED")
        print(f"{'=' * 60}")
        print(f"\n{e}")
        print(f"\nPlease fix the issues above and try again.")
        sys.exit(1)

    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"❌ ERROR")
        print(f"{'=' * 60}")
        print(f"\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
