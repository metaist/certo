# certo claim

## Create a claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim add "Test claim"
```

**Expected**

```
Created claim:
```

## Create a claim with options

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim add "Test claim" --level block --tags foo,bar --why "Because reasons"
```

**Expected**

```
Created claim:
```

## Create claim with no spec

```bash
certo claim add "Test claim"
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Create duplicate claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-8ba75d3"
text = "Test claim"
```

```bash
certo claim add "Test claim"
```

**Exit Code:** 1

**Expected Stderr**

```
already exists
```

## Confirm a claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-8ba75d3"
text = "Test claim"
status = "pending"
```

```bash
certo claim confirm c-8ba75d3
```

**Expected**

```
Confirmed: c-8ba75d3
```

## Confirm already confirmed claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-8ba75d3"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim confirm c-8ba75d3
```

**Expected**

```
already confirmed
```

## Confirm non-existent claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim confirm c-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Reject a claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-8ba75d3"
text = "Test claim"
status = "pending"
```

```bash
certo claim reject c-8ba75d3
```

**Expected**

```
Rejected: c-8ba75d3
```

## Reject already rejected claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-8ba75d3"
text = "Test claim"
status = "rejected"
```

```bash
certo claim reject c-8ba75d3
```

**Expected**

```
already rejected
```

## Reject non-existent claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim reject c-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Create claim with JSON output

```toml
[spec]
name = "test"
version = 1
```

```bash
certo --format json claim add "Test claim"
```

**Expected**

```
"id":
"text": "Test claim"
```

## List claims

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "First claim"
status = "confirmed"

[[claims]]
id = "c-def5678"
text = "Second claim"
status = "pending"
```

```bash
certo claim list
```

**Expected**

```
c-abc1234
c-def5678
```

## List claims filtered by status

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "First claim"
status = "confirmed"

[[claims]]
id = "c-def5678"
text = "Second claim"
status = "pending"
```

```bash
certo claim list --status pending
```

**Expected**

```
c-def5678
```

**Not Expected**

```
c-abc1234
```

## View a claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"
level = "block"
author = "tester"
```

```bash
certo claim view c-abc1234
```

**Expected**

```
ID:      c-abc1234
Text:    Test claim
Status:  confirmed
Level:   block
Author:  tester
```

## View non-existent claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim view c-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Show claim help

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim
```

**Expected**

```
usage:
```

## List claims empty

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim list
```

**Expected**

```
No claims found
```

## List claims no spec

```bash
certo claim list
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## View claim no spec

```bash
certo claim view c-xxx
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Confirm claim no spec

```bash
certo claim confirm c-xxx
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Reject claim no spec

```bash
certo claim reject c-xxx
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## List claims quiet mode

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim list -q
```

**Not Expected**

```
c-abc1234
```

## View claim quiet mode

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim view c-abc1234 -q
```

**Not Expected**

```
ID:
```

## View claim with all fields

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"
level = "block"
author = "tester"
tags = ["foo", "bar"]
why = "Because reasons"
created = 2024-01-01T00:00:00Z
updated = 2024-01-02T00:00:00Z

[[claims.checks]]
kind = "shell"
cmd = "echo test"
```

```bash
certo claim view c-abc1234
```

**Expected**

```
ID:      c-abc1234
Text:    Test claim
Status:  confirmed
Level:   block
Author:  tester
Tags:    foo, bar
Why:     Because reasons
Checks:  1
Created:
Updated:
```
