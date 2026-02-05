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

### `certo check`

Verify the blueprint against code.

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
- `2` - Error (e.g., blueprint not found)

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

- `CERTO_MODEL` - Default LLM model for all tasks (default: `anthropic/claude-sonnet-4`)
- `OPENROUTER_API_KEY` - API key for OpenRouter (required for LLM checks)
