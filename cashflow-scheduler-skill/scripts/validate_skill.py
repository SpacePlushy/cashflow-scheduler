#!/usr/bin/env python3
"""Quick skill validation without packaging.

Usage:
    python scripts/validate_skill.py <path/to/skill>

Example:
    python scripts/validate_skill.py .
"""

import sys
from pathlib import Path

# Import from package_skill
from package_skill import validate_skill, check_optional_resources, ValidationError


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    skill_path = Path(sys.argv[1])

    # Validate skill path exists
    if not skill_path.exists():
        print(f"❌ Error: Skill path does not exist: {skill_path}")
        sys.exit(1)

    if not skill_path.is_dir():
        print(f"❌ Error: Skill path is not a directory: {skill_path}")
        sys.exit(1)

    print(f"{'=' * 60}")
    print(f"VALIDATING SKILL: {skill_path.name}")
    print(f"{'=' * 60}\n")

    try:
        name, description = validate_skill(skill_path)
        check_optional_resources(skill_path)

        print(f"\n{'=' * 60}")
        print(f"✅ VALIDATION PASSED")
        print(f"{'=' * 60}")
        print(f"\nSkill '{name}' is ready for packaging!")
        print(f"\nTo package:")
        print(f"  python scripts/package_skill.py {skill_path}")

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
