# Cashflow Scheduler Skill Analysis Report

## Executive Summary

After using `init_skill.py` to create a base skill template and examining Python scripts across multiple skills in the Anthropic repository, I've identified key patterns and recommendations for the cashflow-scheduler skill.

## What init_skill.py Creates

Running `/skills/skill-creator/scripts/init_skill.py cashflow-scheduler --path .` generates:

```
cashflow-scheduler/
├── SKILL.md (86 lines)
│   ├── YAML frontmatter (name + description TODO)
│   ├── Overview section
│   ├── Structuring guidance (4 pattern types)
│   └── Resources section explaining scripts/, references/, assets/
├── scripts/
│   └── example.py (24 lines) - Placeholder Python script
├── references/
│   └── api_reference.md (61 lines) - Placeholder reference doc
└── assets/
    └── example_asset.txt (27 lines) - Placeholder asset file
```

**Key Insight:** The template includes extensive TODO guidance and structuring patterns that should be deleted after filling in actual content.

## Python Scripts Analysis - Patterns Found

### 1. PDF Skill Scripts (Highly Relevant Pattern)

**Location:** `/skills/document-skills/pdf/scripts/`

**Scripts examined:**
- `fill_fillable_fields.py` (115 lines)
- `extract_form_field_info.py` (153 lines)

**Pattern:** **Two-script workflow for complex operations**
- Script 1: Extract metadata/structure → JSON output
- Script 2: Process using extracted metadata + user input → Final output

**Example:**
```bash
# Step 1: Extract form fields from PDF
python extract_form_field_info.py input.pdf fields.json

# Step 2: Claude fills in the JSON, then:
python fill_fillable_fields.py input.pdf filled_fields.json output.pdf
```

**Why this works:**
1. Deterministic data extraction (avoid LLM hallucination)
2. JSON intermediate format Claude can easily manipulate
3. Separation of concerns (read vs write)
4. Error validation built into both steps

**Relevance to cashflow-scheduler:** ✅ HIGH
- Our solver workflow is already similar: read plan.json → solve → write schedule
- We can extract this pattern into scripts

### 2. PPTX Thumbnail Script (Complex CLI Tool)

**Location:** `/skills/document-skills/pptx/scripts/thumbnail.py`

**Size:** 451 lines

**Pattern:** **Full-featured CLI tool with argparse**
- Detailed docstring explaining usage and examples
- Multiple command-line options (--cols, --outline-placeholders)
- Comprehensive error handling
- Progress output to stdout
- Multiple output files with smart naming

**Example usage:**
```bash
python thumbnail.py presentation.pptx grid --cols 4
# Creates: grid-1.jpg, grid-2.jpg, grid-3.jpg
```

**Relevance to cashflow-scheduler:** ⚠️ MEDIUM
- Our CLI tool already exists (`./cash`)
- Could create helper scripts for specific workflows

### 3. Artifacts Builder Scripts (Bash Automation)

**Location:** `/skills/artifacts-builder/scripts/`

**Scripts:**
- `init-artifact.sh` - Project scaffolding
- `bundle-artifact.sh` - Build and packaging

**Pattern:** **Bash scripts for multi-step automation**
- Environment detection (Node version, OS)
- Dependency checking and installation
- File manipulation and configuration
- Progressive output with emoji indicators

**Relevance to cashflow-scheduler:** ⚠️ MEDIUM
- Could create setup/install helpers
- Phase B scripts might follow this pattern

### 4. Slack GIF Creator (Python Module Structure)

**Location:** `/skills/slack-gif-creator/`

**Structure:**
```
core/                  # Reusable modules
├── typography.py
├── validators.py
├── easing.py
├── visual_effects.py
├── gif_builder.py
├── frame_composer.py
└── color_palettes.py

templates/             # Example implementations
├── pulse.py
├── wiggle.py
└── kaleidoscope.py
```

**Pattern:** **Python package instead of standalone scripts**
- Core library modules in `core/`
- Template/example files in `templates/`
- No `scripts/` directory - Claude imports and uses the package

**Relevance to cashflow-scheduler:** ❌ LOW
- Our cashflow package already exists as Python package
- This is more for skills that need to bundle code Claude will write inline

## Key Findings for Cashflow Scheduler

### Finding 1: Most Skills DON'T Have Scripts

Of the skills reviewed:
- **artifacts-builder** (73 lines SKILL.md): 2 bash scripts
- **brand-guidelines** (74 lines SKILL.md): NO scripts
- **pdf** (294 lines SKILL.md): 7+ Python scripts
- **pptx** (483 lines SKILL.md): 4+ Python scripts
- **slack-gif-creator** (646 lines SKILL.md): Python package (not scripts/)
- **mcp-builder** (328 lines SKILL.md): NO scripts
- **algorithmic-art** (404 lines SKILL.md): NO scripts (uses p5.js in-place)

**Conclusion:** Scripts are the exception, not the rule. Most skills rely on SKILL.md to guide Claude in using existing tools.

### Finding 2: Scripts Serve Specific Purposes

When scripts exist, they solve these problems:

1. **Deterministic operations** - PDF form field extraction, image conversion
2. **Complex multi-step workflows** - Build/bundle pipelines
3. **Avoiding repeated code generation** - Boilerplate that Claude would rewrite every time
4. **External tool integration** - Wrapping soffice, pdftoppm, etc.

### Finding 3: The PDF Pattern Matches Our Use Case

The PDF skill's two-script pattern is remarkably similar to what we need:

**PDF Workflow:**
```
PDF → extract_form_field_info.py → fields.json
           ↓ (Claude edits JSON)
fields.json + PDF → fill_fillable_fields.py → filled.pdf
```

**Cashflow Workflow (Current):**
```
User input → (Claude creates plan.json manually)
plan.json → ./cash solve → schedule output
```

**Potential Cashflow Workflow (with scripts):**
```
User interview → create_plan.py → plan.json
plan.json → ./cash solve → schedule output
plan.json + day/balance → set_eod_helper.py → updated_plan.json
```

## Recommendations

### For Phase A (Current - Documentation Only)

**DO NOT add scripts yet.** Here's why:

1. **Original skill (509 lines SKILL.md) violated progressive disclosure**
   - Too much detail in SKILL.md
   - Duplicated reference docs

2. **Revised skill (239 lines SKILL.md) follows the majority pattern**
   - Lean SKILL.md with workflow guidance
   - Detailed docs in references/
   - No scripts - guides Claude to use existing `./cash` CLI

3. **Most comparable skills have no scripts:**
   - brand-guidelines: 74 lines, NO scripts
   - artifacts-builder: 73 lines, 2 scripts for project scaffolding

**Phase A Recommendation:** ✅ Use the revised skill (cashflow-scheduler-revised.zip)
- Follows skill-creator guidelines
- Matches patterns from successful minimal skills
- References point to detailed docs only when needed

### For Phase B (Automation Scripts)

When moving to Phase B, add scripts following the PDF skill pattern:

#### Script 1: `scripts/create_plan.py` (Interactive Plan Builder)
```python
#!/usr/bin/env python3
"""
Interactive plan creation wizard for cashflow-scheduler.

Guides users through creating a valid plan.json by asking questions
about their financial situation.

Usage:
    create_plan.py [--output plan.json] [--month YYYY-MM]

Example:
    python scripts/create_plan.py --output october.json
"""
# Interactive prompts for:
# - Start balance
# - Target end balance
# - Deposits (recurring pattern detection)
# - Bills (recurring pattern detection)
# - Rent guard calculation
# - Band recommendation
```

**Size estimate:** 150-200 lines (similar to extract_form_field_info.py)

#### Script 2: `scripts/analyze_plan.py` (Feasibility Pre-Check)
```python
#!/usr/bin/env python3
"""
Analyze plan.json feasibility before running solver.

Performs quick math checks to identify obvious infeasibility
without running the full solver.

Usage:
    analyze_plan.py plan.json

Outputs:
    - Feasibility assessment (likely feasible / likely infeasible)
    - Specific issues found
    - Recommendations to fix
"""
# Quick checks:
# - Total bills vs deposits + max work earnings
# - Rent guard achievability
# - Day 1 solvency
```

**Size estimate:** 100-150 lines

#### Script 3: `scripts/explain_infeasible.py` (Diagnostic Tool)
```python
#!/usr/bin/env python3
"""
Deep diagnostic for infeasible plans.

Runs binary search to find minimal infeasible subset of constraints.

Usage:
    explain_infeasible.py plan.json

Example output:
    "Plan becomes feasible if you:
     - Remove bill 'Rent' on day 30, OR
     - Add $300 more to start_balance, OR
     - Lower target_end by $200"
"""
```

**Size estimate:** 200-250 lines (complex logic)

#### Script 4: `scripts/month_rollover.py` (Automated Rollover)
```python
#!/usr/bin/env python3
"""
Generate next month's plan from current month's solution.

Usage:
    month_rollover.py current_plan.json --solved-schedule schedule.json --output next_month.json

Uses current month's closing balance as next month's start_balance.
Optionally copies recurring bills/deposits with date shifting.
"""
```

**Size estimate:** 100-150 lines

### Directory Structure for Phase B

```
cashflow-scheduler/
├── SKILL.md (250-300 lines)
│   ├── Overview
│   ├── Quick Start (using scripts)
│   ├── Essential Workflows
│   │   ├── Create Plan (using create_plan.py)
│   │   ├── Solve Plan (using ./cash)
│   │   ├── Analyze Plan (using analyze_plan.py)
│   │   └── Month Rollover (using month_rollover.py)
│   ├── Troubleshooting (brief, points to references)
│   └── Constraint System (brief, points to references)
├── scripts/
│   ├── create_plan.py (150-200 lines)
│   ├── analyze_plan.py (100-150 lines)
│   ├── explain_infeasible.py (200-250 lines)
│   ├── month_rollover.py (100-150 lines)
│   └── compare_solvers.py (75-100 lines)
├── references/
│   ├── plan_schema.md (unchanged)
│   ├── troubleshooting.md (unchanged)
│   ├── solver_comparison.md (unchanged)
│   └── constraints.md (unchanged)
└── assets/
    └── example_plans/ (unchanged)
```

**Total Phase B estimates:**
- SKILL.md: +50 lines (add script usage sections)
- scripts/: 625-850 lines total
- Total skill: 2,800-3,000 lines

## Comparison: Original vs Revised vs Phase B

| Aspect | Original | Revised (Phase A) | Phase B |
|--------|----------|-------------------|---------|
| **SKILL.md** | 509 lines | 239 lines | ~280 lines |
| **Scripts** | 0 | 0 | 5 scripts (650 lines) |
| **References** | 1,730 lines | 1,730 lines | 1,730 lines |
| **Total** | 2,239 lines | 1,969 lines | 2,660 lines |
| **Duplication** | Yes (SKILL.md duplicates references) | No | No |
| **Pattern** | Monolithic SKILL.md | Lean + references | Lean + scripts + references |
| **Follows Guidelines** | ❌ No | ✅ Yes | ✅ Yes |

## Final Recommendation

### Immediate Action (Phase A)
**Use cashflow-scheduler-revised.zip**

Reasons:
1. ✅ Follows skill-creator guidelines (no duplication)
2. ✅ Matches successful minimal skill patterns (brand-guidelines, artifacts-builder)
3. ✅ Under 5k word limit for SKILL.md
4. ✅ Progressive disclosure (references loaded as needed)
5. ✅ All content quality preserved (just reorganized)

### Phase B Transition
When ready to add automation (estimated 2-3 weeks later):

1. **Keep SKILL.md lean** - Add workflow sections, not implementation details
2. **Follow PDF skill pattern** - Two-phase scripts (extract → manipulate → apply)
3. **Start with create_plan.py** - Highest user value (eliminates manual JSON writing)
4. **Add diagnostic scripts next** - analyze_plan.py and explain_infeasible.py
5. **Finish with automation** - month_rollover.py and compare_solvers.py

### What NOT to Do

❌ **Don't create a Python package structure** (like slack-gif-creator)
- The cashflow package already exists in the main repo
- Skills should use existing tools, not duplicate them

❌ **Don't add scripts to Phase A**
- Violates the minimal skill pattern
- Adds unnecessary complexity
- Scripts should solve clear pain points (Phase B)

❌ **Don't put implementation details in SKILL.md**
- Keep detailed algorithms, schemas, and examples in references/
- SKILL.md should be workflow-focused, not reference-focused

## Conclusion

The revised Phase A skill (239 lines SKILL.md, no scripts) correctly follows Anthropic's skill-creator patterns. When moving to Phase B, add scripts following the PDF skill's two-phase pattern, focusing on interactive plan creation and diagnostic tools.

The init_skill.py template provides a starting structure, but the real patterns emerge from studying successful skills like pdf (scripts for deterministic operations) and brand-guidelines (minimal SKILL.md with no scripts when existing tools suffice).
