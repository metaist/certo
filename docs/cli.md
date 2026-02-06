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
- `--version` - Print version and exit (top-level only)

## Commands

### `certo status`

Show the current state of the spec.

```bash
certo status [path] [id] [options]
```

**Arguments:**

- `path` - Project root (default: current directory)
- `id` - Specific item ID to show (e.g., c-abc1234, i-abc1234, x-abc1234)

**Options:**

- `--claims` - Show only claims
- `--issues` - Show only issues
- `--contexts` - Show only contexts

**Examples:**

```bash
certo status                       # Show all
certo status --claims              # Show only claims
certo status . c-e50e9d4           # Show specific claim
certo status -v                    # Verbose output
certo status --format json         # JSON output
```

### `certo check`

Verify the spec against code.

```bash
certo check [path] [options]
```

**Arguments:**

- `path` - Project root (default: current directory)

**Options:**

- `--offline` - Skip LLM-backed checks (no network calls)
- `--no-cache` - Ignore cached verification results
- `--model MODEL` - LLM model to use (overrides `CERTO_MODEL` env var)

**Exit codes:**

- `0` - All checks passed
- `1` - One or more checks failed
- `2` - Error (e.g., spec not found)

### `certo scan`

Discover assumptions and check consistency.

```bash
certo scan [path]
```

**Arguments:**

- `path` - Project root (default: current directory)

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
