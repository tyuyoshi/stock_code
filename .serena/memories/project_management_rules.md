# GitHub Project Management Rules

## Critical Rules for Issue Management

### 1. All Issues MUST be Added to Project Board

**Project**: https://github.com/users/tyuyoshi/projects/5  
**Project ID**: 5  
**Owner**: tyuyoshi

**Rule**: Every new issue created MUST be immediately added to the project board. No exceptions.

### 2. Standard Issue Creation Workflow

```bash
# Step 1: Create the issue
gh issue create --repo tyuyoshi/stock_code --title "..." --body "..."

# Step 2: Get the issue number (latest created issue)
ISSUE_NUM=$(gh issue list --repo tyuyoshi/stock_code --limit 1 --json number --jq '.[0].number')

# Step 3: Add to Project board #5 (REQUIRED!)
gh project item-add 5 --owner tyuyoshi --url https://github.com/tyuyoshi/stock_code/issues/$ISSUE_NUM
```

### 3. Required GitHub CLI Scopes

For issue management, you need TWO scopes:

```bash
# Read-only access to project data (for verification)
gh auth refresh -s read:project

# Write access to add items to project board (REQUIRED for adding issues)
gh auth refresh -s project
```

**Important**: The `project` scope is necessary for `gh project item-add` command.

### 4. Verification Commands

Before starting work, verify all open issues are tracked:

```bash
# List issues in project board
gh project item-list 5 --owner tyuyoshi --format json --limit 1000 | jq '[.items[].content.number] | sort'

# List all open issues
gh issue list --repo tyuyoshi/stock_code --limit 1000 --json number --state open --jq '[.[].number] | sort'

# Compare and find untracked issues (bash)
comm -13 \
  <(gh project item-list 5 --owner tyuyoshi --format json --limit 1000 | jq -r '[.items[].content.number] | sort | .[]') \
  <(gh issue list --repo tyuyoshi/stock_code --limit 1000 --json number --state open --jq -r '[.[].number] | sort | .[]')
```

### 5. Bulk Adding Untracked Issues

If you find issues not in the project board:

```bash
# Add multiple issues (replace with actual issue numbers)
for issue in 23 24 25 26; do 
  echo "Adding issue #$issue..."
  gh project item-add 5 --owner tyuyoshi --url https://github.com/tyuyoshi/stock_code/issues/$issue
done
```

## Historical Context

### 2025/11/09 Project Cleanup

**Problem**: 32 open issues were not tracked in project board
- Issues #23-26, #38, #55-57, #86-87, #89-96, #98-107, #109, #111-115
- These were created after major PRs (#105, #110) without project tracking

**Solution**: Bulk added all 32 issues to project board

**Root Cause**: No enforced workflow for adding issues to project board

**Prevention**: 
1. Updated CLAUDE.md with mandatory workflow
2. Created this memory file for future reference
3. Claude Code will now always use 3-step process for issue creation

## Claude Code Instructions

When creating a new issue:
1. ✅ **ALWAYS** use the 3-step workflow above
2. ✅ **VERIFY** issue was added to project board
3. ✅ **NEVER** skip step 3 (adding to project board)
4. ✅ If permission error, instruct user to run `gh auth refresh -s project`

When asked to audit project management:
1. Run verification commands to compare project board vs open issues
2. Report any untracked issues
3. Offer to bulk add them to project board

## References

- **CLAUDE.md**: Lines 190-232 contain the official workflow
- **GitHub Project Board**: https://github.com/users/tyuyoshi/projects/5
- **Repository**: https://github.com/tyuyoshi/stock_code

## Success Metrics (2025/11/09)

- ✅ 32 untracked issues added to project board
- ✅ 100% of open issues now tracked in project
- ✅ Workflow documented in CLAUDE.md
- ✅ Memory created for future sessions

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>
