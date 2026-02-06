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

- `id` - Specific item ID to show (e.g., c-xxx, i-xxx, x-xxx)

**Options:**

- `--claims` - Show only claims
- `--issues` - Show only issues
- `--contexts` - Show only contexts

**Examples:**

```bash
certo status                       # Show all
certo status --claims              # Show only claims
certo status c-e50e9d4             # Show specific claim
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

### `certo context`

Manage contexts. Running `certo context` without a subcommand displays help.

#### `certo context add`

Create a new context.

```bash
certo context add "name" [options]
```

**Options:**

- `--description DESC` - Context description

#### `certo context list`

List all contexts.

```bash
certo context list [options]
```

**Options:**

- `--status {enabled,disabled}` - Filter by status

#### `certo context view`

View a specific context.

```bash
certo context view ID
```

#### `certo context on`

Enable a context.

```bash
certo context on ID
```

#### `certo context off`

Disable a context.

```bash
certo context off ID
```

### `certo check`

Verify the spec against code.

```bash
certo check [options]
```

**Options:**

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
