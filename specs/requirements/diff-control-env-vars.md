# SRS: Diff Control Environment Variables

## Feature Overview

**Feature ID:** F-003-diff-control-env-vars
**Status:** Proposed
**Created:** 2026-02-02

## Purpose

Provide environment variables to control diff output behavior in batou deployments. This allows users to reduce diff noise for generated files and optionally override sensitive data hiding.

## Functional Requirements

### REQ-FUNC-003-001: BATOU_SHOW_DIFF Environment Variable

The `BATOU_SHOW_DIFF` environment variable controls diff output verbosity.

**Valid values:**
- `full`: Show complete unified diffs (current default behavior)
- `summary`: Show only changed file list without diff content
- `none`: Suppress all diff output

**Default:** `full`

**Behavior:**
- When not set, defaults to `full` (current behavior unchanged)
- When set to invalid value, batou should warn and default to `full`
- Applies to all file diff operations during deployment
- Does NOT affect deployment execution, only output

**Example summary output:**
```
changed: work/myapp/pod-1.yaml (r:0, w:1)
changed: work/myapp/pod-2.yaml (r:0, w:1)
changed: work/myapp/pod-3.yaml (r:0, w:1)
Updated 3 files
```

**Example none output:**
```
Updated 3 files
```

### REQ-FUNC-003-002: BATOU_SHOW_SECRET_DIFFS Environment Variable

The `BATOU_SHOW_SECRET_DIFFS` environment variable overrides sensitive data detection.

**Valid values:**
- `1` or `true` (case-insensitive): Show diffs for files containing secret data
- Not set or any other value: Respect `sensitive_data` flag (current behavior)

**Default:** Not set (respects sensitive_data flag)

**Behavior:**
- When set to `1` or `true`, overrides `sensitive_data=True` flag on File components
- Enables diff display for files that would normally be hidden
- Does NOT affect actual secret encryption or security
- Does NOT affect file content or deployment behavior

**Security Considerations:**
- This is an EXPLICIT override that requires user action
- Should trigger a warning in startup logging
- Should NOT be enabled by default in production environments

### REQ-FUNC-003-003: Startup Logging for Behavior-Changing Environment Variables

Batou MUST display all behavior-changing environment variables at startup.

**Behavior:**
- Displayed BEFORE any deployment operations begin
- Displayed AFTER argument parsing
- Displayed REGARDLESS of debug mode (-d flag)
- Must be visible in normal terminal output

**Required logging:**
```bash
$ ./batou deploy dev
[INFO] BATOU_SHOW_DIFF=summary - diff output reduced to file list
[INFO] BATOU_SHOW_SECRET_DIFFS=1 - sensitive data diffs enabled (WARNING)
Deploying to dev...
```

**Logging requirements:**
- Format: `[INFO] <ENV_VAR>=<value> - <description>`
- Use yellow color for WARNING messages (e.g., BATOU_SHOW_SECRET_DIFFS)
- Only display ENV vars that are actually set
- Do NOT display default behavior (e.g., "BATOU_SHOW_DIFF=full" when not set)

### REQ-FUNC-003-004: Diff Control for File Component

The File component's `verify()` method MUST respect `BATOU_SHOW_DIFF` setting.

**Implementation requirements:**
- Read `BATOU_SHOW_DIFF` from environment at diff generation time
- Skip diff generation when mode is `none`
- Generate file list only when mode is `summary`
- Generate full unified diff when mode is `full` (default)

**Interaction with sensitive_data:**
- Apply `BATOU_SHOW_DIFF` mode AFTER sensitive_data check
- When `BATOU_SHOW_SECRET_DIFFS` is set, disable sensitive_data filtering
- When `BATOU_SHOW_SECRET_DIFFS` is NOT set, respect `sensitive_data` flag

**Flow:**
```
1. Check if file contains sensitive data
2. Check BATOU_SHOW_SECRET_DIFFS override
3. If secret and no override: show warning message, skip diff
4. If not secret or override: check BATOU_SHOW_DIFF mode
5. Generate output according to mode (full/summary/none)
```

### REQ-FUNC-003-005: Backward Compatibility

Default behavior MUST remain unchanged from current batou implementation.

**Requirements:**
- Without ENV vars set, behavior identical to current batou
- Existing deployments continue to work without changes
- No breaking changes to API or configuration
- All existing diff behavior preserved as default

## Non-Functional Requirements

### NFR-USE-003-001: User Experience

Users should be able to quickly identify deployment changes without diff noise from generated files.

### NFR-USE-003-002: Security

`BATOU_SHOW_SECRET_DIFFS` must not enable accidental exposure of secrets. Users must explicitly set this ENV var to override protection.

### NFR-OBS-003-001: Observability

All behavior-altering ENV vars must be visible at startup to prevent surprises during deployment.

## Use Cases

### UC-003-001: Reduce Diff Noise for Generated Files

**Scenario:** User has 50 generated YAML files that are rewritten every deployment with only minor formatting changes.

**User action:** Sets `BATOU_SHOW_DIFF=summary`

**Expected result:**
- File list shows all 50 files changed
- No -100/+100 diff lines displayed
- User can see which files changed without noise

### UC-003-002: Debug Deployment with Full Diffs

**Scenario:** User needs to understand detailed changes in deployment.

**User action:** Default behavior (no ENV var set) or explicitly `BATOU_SHOW_DIFF=full`

**Expected result:**
- Complete unified diffs displayed
- Full context for all changes

### UC-003-003: Override Sensitive Data Protection for Debugging

**Scenario:** User is debugging a deployment where files are incorrectly marked as sensitive.

**User action:** Sets `BATOU_SHOW_SECRET_DIFFS=1`

**Expected result:**
- Sensitive protection warning displayed at startup
- Diffs shown for all files including those marked sensitive
- User can verify changes manually

## Acceptance Criteria

- [ ] `BATOU_SHOW_DIFF=summary` shows file list only
- [ ] `BATOU_SHOW_DIFF=none` shows no diff output
- [ ] `BATOU_SHOW_DIFF=full` shows complete diffs (default)
- [ ] `BATOU_SHOW_SECRET_DIFFS=1` overrides sensitive_data flag
- [ ] All behavior-changing ENV vars displayed at startup
- [ ] Default behavior unchanged (backward compatibility)
- [ ] Invalid values fall back to `full` with warning
- [ ] Sensitive override displays warning at startup
