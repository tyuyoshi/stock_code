# Session Rules: One Issue Per Session

**Rule Established**: 2025-11-09

## Core Principle
**1 Session = 1 Issue**

## Guidelines

### Session Scope
- Each development session should focus on completing **exactly one GitHub Issue**
- Do not attempt to work on multiple issues in a single session
- Complete all aspects of the issue (implementation, testing, documentation, PR) before ending

### Benefits
1. **Focus**: Clear, singular objective for each session
2. **Quality**: Complete, well-tested solutions
3. **Tracking**: Clean commit history and PR-to-issue mapping
4. **Review**: Easier code review with focused changes

### Workflow
1. Select one issue at session start
2. Create feature branch for that issue
3. Implement solution
4. Write/update tests
5. Commit and create PR
6. Update memory files
7. End session

### Exceptions
- Bug fixes discovered during implementation of current issue
- Code style/formatting fixes in modified files
- Documentation updates for current issue

## Implementation History
- **First Session**: Issue #125 (WebSocket Memory Leak) - 2025-11-09
  - Complete implementation in ~3 hours
  - 19 tests passing
  - PR #132 created

## Memory Management
- Update session memory files at end of each session
- Document completion status and next steps
- Maintain project overview accuracy
