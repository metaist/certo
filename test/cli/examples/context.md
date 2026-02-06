# certo context

## Create a context

```toml
[spec]
name = "test"
version = 1
```

```bash
certo context add "release"
```

**Expected**

```
Created context:
```

## Create a context with description

```toml
[spec]
name = "test"
version = 1
```

```bash
certo context add "release" --description "For release builds"
```

**Expected**

```
Created context:
```

## Create context with no spec

```bash
certo context add "release"
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Create duplicate context

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-a4d451e"
name = "release"
```

```bash
certo context add "release"
```

**Exit Code:** 1

**Expected Stderr**

```
already exists
```

## Create context with JSON output

```toml
[spec]
name = "test"
version = 1
```

```bash
certo --format json context add "release"
```

**Expected**

```
"id":
"name": "release"
```

## List contexts

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "release"
enabled = true

[[contexts]]
id = "x-def5678"
name = "debug"
enabled = false
```

```bash
certo context list
```

**Expected**

```
x-abc1234
x-def5678
```

## List enabled contexts

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "release"
enabled = true

[[contexts]]
id = "x-def5678"
name = "debug"
enabled = false
```

```bash
certo context list --status enabled
```

**Expected**

```
x-abc1234
```

**Not Expected**

```
x-def5678
```

## View a context

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "release"
description = "For releases"
enabled = true
```

```bash
certo context view x-abc1234
```

**Expected**

```
ID:          x-abc1234
Name:        release
Description: For releases
Enabled:     True
```

## View non-existent context

```toml
[spec]
name = "test"
version = 1
```

```bash
certo context view x-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Enable a context

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "release"
enabled = false
```

```bash
certo context on x-abc1234
```

**Expected**

```
Enabled: x-abc1234
```

## Enable already enabled context

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "release"
enabled = true
```

```bash
certo context on x-abc1234
```

**Expected**

```
already enabled
```

## Disable a context

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "release"
enabled = true
```

```bash
certo context off x-abc1234
```

**Expected**

```
Disabled: x-abc1234
```

## Disable already disabled context

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "release"
enabled = false
```

```bash
certo context off x-abc1234
```

**Expected**

```
already disabled
```

## Enable non-existent context

```toml
[spec]
name = "test"
version = 1
```

```bash
certo context on x-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Show context help

```toml
[spec]
name = "test"
version = 1
```

```bash
certo context
```

**Expected**

```
usage:
```

## List contexts empty

```toml
[spec]
name = "test"
version = 1
```

```bash
certo context list
```

**Expected**

```
No contexts found
```

## List contexts no spec

```bash
certo context list
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## View context no spec

```bash
certo context view x-xxx
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Enable context no spec

```bash
certo context on x-xxx
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Disable context no spec

```bash
certo context off x-xxx
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Disable non-existent context

```toml
[spec]
name = "test"
version = 1
```

```bash
certo context off x-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## List contexts quiet mode

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "release"
enabled = true
```

```bash
certo context list -q
```

**Not Expected**

```
x-abc1234
```

## View context quiet mode

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "release"
enabled = true
```

```bash
certo context view x-abc1234 -q
```

**Not Expected**

```
ID:
```

## List disabled contexts

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "release"
enabled = true

[[contexts]]
id = "x-def5678"
name = "debug"
enabled = false
```

```bash
certo context list --status disabled
```

**Expected**

```
x-def5678
```

**Not Expected**

```
x-abc1234
```

## View context with updated field

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-test"
scope = "*.py"
status = "active"
created = 2025-01-01T00:00:00Z
updated = 2025-01-02T00:00:00Z
```

```bash
certo context view x-test
```

**Expected**

```
Updated:     2025-01-02
```
