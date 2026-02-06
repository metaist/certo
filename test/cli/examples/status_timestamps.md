# status - Timestamps and Optional Fields

## Claim with timestamps

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
created = 2026-02-05T12:00:00Z
updated = 2026-02-06T14:30:00Z
```

```bash
certo status c-abc1234
```

**Expected**

```
Created: 2026-02-05 12:00
Updated: 2026-02-06 14:30
```

## Claim with evidence and traces

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
evidence = ["pyproject.toml:5", "README.md:10"]
traces_to = ["c-parent1", "c-parent2"]
supersedes = "c-old1234"
```

```bash
certo status c-abc1234
```

**Expected**

```
Evidence:
  - pyproject.toml:5
  - README.md:10
Traces to: c-parent1, c-parent2
Supersedes: c-old1234
```

## Issue with timestamps

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Test issue"
created = 2026-02-05T12:00:00Z
updated = 2026-02-06T14:30:00Z
```

```bash
certo status i-abc1234
```

**Expected**

```
Created: 2026-02-05 12:00
Updated: 2026-02-06 14:30
```

## Context with timestamps

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "Test context"
created = 2026-02-05T12:00:00Z
updated = 2026-02-06T14:30:00Z
```

```bash
certo status x-abc1234
```

**Expected**

```
Created: 2026-02-05 12:00
Updated: 2026-02-06 14:30
```

## Context with topic modification

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "Test context"
modifications = [{ action = "promote", topic = "security" }]
```

```bash
certo status x-abc1234
```

**Expected**

```
Modifications:
  - topic=security: promote
```

## Context with level modification

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "Test context"
modifications = [{ action = "promote", level = "warn" }]
```

```bash
certo status x-abc1234
```

**Expected**

```
Modifications:
  - level=warn: promote
```

## Context with empty modification

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "Test context"
modifications = [{ action = "relax" }]
```

```bash
certo status x-abc1234
```

**Expected**

```
Modifications:
  - (unknown): relax
```
