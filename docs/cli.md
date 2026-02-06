# CLI Reference

## Global Options

These options can be used with any command, either before or after the subcommand:

```bash
certo -q check        # quiet before subcommand
certo check -q        # quiet after subcommand
```

- `-q, --quiet` - Only show issues, no output on success
- `-v, --verbose` - Show detailed output
- `--format {text,json}` - Output format (default: text)
- `--path PATH` - Project root (default: current directory)
- `--version` - Print version and exit (top-level only)

## Commands

### `certo init`

Initialize a new certo spec.

```bash
certo init [options]
```

**Options:**

- `--name NAME` - Project name (default: directory name)
- `--force` - Overwrite existing spec

### `certo status`

Show the current state of the spec.

```bash
certo status [id] [options]
```

**Arguments:**

- `id` - Specific item ID to show (e.g., c-xxx, i-xxx, k-xxx)

**Options:**

- `--claims` - Show only claims
- `--issues` - Show only issues
- `--checks` - Show only checks

**Examples:**

```bash
certo status                       # Show all
certo status --claims              # Show only claims
certo status k-test                # Show specific check
certo status -v                    # Verbose output
certo status --format json         # JSON output
```

### `certo claim`

Manage claims. Running `certo claim` without a subcommand displays help.

#### `certo claim add`

Create a new claim.

```bash
certo claim add "claim text" [options]
```

**Options:**

- `--level {block,warn,skip}` - Importance level (default: warn)
- `--tags TAGS` - Comma-separated tags
- `--why REASON` - Rationale for the claim
- `--closes IDS` - Comma-separated issue IDs to close
- `--author NAME` - Author name

#### `certo claim list`

List all claims.

```bash
certo claim list [options]
```

**Options:**

- `--status {pending,confirmed,rejected,superseded}` - Filter by status

#### `certo claim view`

View a specific claim.

```bash
certo claim view ID
```

#### `certo claim confirm`

Confirm a pending claim.

```bash
certo claim confirm ID
```

#### `certo claim reject`

Reject a claim.

```bash
certo claim reject ID [options]
```

**Options:**

- `--reason REASON` - Reason for rejection

### `certo issue`

Manage issues. Running `certo issue` without a subcommand displays help.

#### `certo issue add`

Create a new issue.

```bash
certo issue add "issue text" [options]
```

**Options:**

- `--tags TAGS` - Comma-separated tags

#### `certo issue list`

List all issues.

```bash
certo issue list [options]
```

**Options:**

- `--status {open,closed}` - Filter by status

#### `certo issue view`

View a specific issue.

```bash
certo issue view ID
```

#### `certo issue close`

Close an issue.

```bash
certo issue close ID [options]
```

**Options:**

- `--reason REASON` - Reason for closing

#### `certo issue reopen`

Reopen a closed issue.

```bash
certo issue reopen ID
```

### `certo check`

Run checks and verify claims. Running `certo check` without arguments runs all checks.

```bash
certo check [subcommand] [options]
```

**Options (for running checks):**

- `--offline` - Skip LLM-backed checks (no network calls)
- `--no-cache` - Ignore cached verification results
- `--model MODEL` - LLM model to use (overrides `CERTO_MODEL` env var)
- `--only IDS` - Run only specific claims/checks (comma-separated IDs)
- `--skip IDS` - Skip specific claims/checks (comma-separated IDs)
- `--output PATH` - Write detailed results to file (use `-` for stdout)

**Exit codes:**

- `0` - All checks passed
- `1` - One or more checks failed
- `2` - Error (e.g., spec not found)

#### `certo check run`

Run verification checks (same as `certo check` with no subcommand).

```bash
certo check run [options]
```

#### `certo check list`

List all checks.

```bash
certo check list [options]
```

**Options:**

- `--status {enabled,disabled}` - Filter by status
- `--kind {shell,llm,fact,url}` - Filter by check kind

#### `certo check show`

View a specific check.

```bash
certo check show ID
```

#### `certo check add`

Add a new check.

```bash
certo check add KIND [options]
```

**Arguments:**

- `KIND` - Check kind: `shell`, `llm`, `fact`, or `url`

**Common options:**

- `--id ID` - Check ID (auto-generated if not provided)
- `--status {enabled,disabled}` - Initial status (default: enabled)

**Options for shell checks:**

- `--cmd CMD` - Shell command to run (required)
- `--exit-code N` - Expected exit code (default: 0)
- `--matches PATTERNS` - Comma-separated patterns that must match
- `--timeout N` - Timeout in seconds (default: 60)

**Options for llm checks:**

- `--files PATTERNS` - Comma-separated file patterns (required)
- `--prompt TEXT` - Verification prompt

**Options for fact checks:**

- `--has KEY` - Fact key that must exist
- `--empty KEY` - Fact key that must be empty
- `--equals KEY` - Fact key that must equal `--value`
- `--value VALUE` - Value to compare against (required with `--equals`)

**Options for url checks:**

- `--url URL` - URL to fetch (required)
- `--cmd CMD` - Shell command to pipe fetched content through

**Examples:**

```bash
# Add a shell check
certo check add shell --cmd "test -f README.md"

# Add an LLM check
certo check add llm --files "src/*.py" --prompt "Verify code quality"

# Add a fact check
certo check add fact --has python.version

# Add a URL check
certo check add url --url https://api.example.com/status --cmd "jq .healthy"
```

#### `certo check remove`

Remove a check.

```bash
certo check remove ID
```

#### `certo check on`

Enable a disabled check.

```bash
certo check on ID
```

#### `certo check off`

Disable a check.

```bash
certo check off ID
```

### `certo scan`

Discover assumptions and check consistency.

```bash
certo scan
```

**Exit codes:**

- `0` - No consistency issues found
- `1` - Consistency issues detected

### `certo kb`

Manage the knowledge base. Running `certo kb` without a subcommand displays help.

#### `certo kb update`

Update knowledge from authoritative sources.

```bash
certo kb update [source]
```

**Arguments:**

- `source` - Specific source to update (optional)
  - `python` - Update Python stdlib knowledge from typeshed
  - If omitted, updates all known sources

## Environment Variables

- `CERTO_MODEL` - Default LLM model for verification (default: `anthropic/claude-sonnet-4`)
- `OPENROUTER_API_KEY` - API key for OpenRouter (required for LLM checks)
