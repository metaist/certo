# status - Detail Views

## Show claim detail

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"
source = "human"
author = "metaist"
level = "block"
tags = ["testing"]
verify = ["static", "llm"]
files = ["README.md"]
why = "Because reasons"
considered = ["alt1", "alt2"]
closes = ["i-xxx"]
created = 2026-02-05T12:00:00Z
```

```bash
certo status c-abc1234
```

**Expected**

```
c-abc1234: Test claim
Status: confirmed
Level: block
Author: metaist
Tags: testing
Why: Because reasons
Considered:
  - alt1
  - alt2
Verify: static, llm
Files:
  - README.md
Closes: i-xxx
```

## Show claim detail - minimal

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Minimal claim"
```

```bash
certo status c-abc1234
```

**Expected**

```
c-abc1234: Minimal claim
Status: pending
Level: warn
Source: human
```

**Not Expected**

```
Why:
Considered:
Closes:
```

## Show issue detail

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Test issue"
status = "closed"
tags = ["architecture"]
closed_reason = "Resolved by c-xxx"
created = 2026-02-05T12:00:00Z
```

```bash
certo status i-abc1234
```

**Expected**

```
i-abc1234: Test issue
Status: closed
Tags: architecture
Closed reason: Resolved by c-xxx
```

## Show issue detail - minimal

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Minimal issue"
```

```bash
certo status i-abc1234
```

**Expected**

```
i-abc1234: Minimal issue
Status: open
```

**Not Expected**

```
Tags:
Closed reason:
```

## Show context detail

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "Test context"
description = "Full context description"
expires = 2026-12-31T00:00:00Z
modifications = [{ action = "relax", claim = "c-xxx" }]
```

```bash
certo status x-abc1234
```

**Expected**

```
x-abc1234: Test context
Full context description
Expires: 2026-12-31
Modifications:
  - c-xxx: relax
```

## Show context detail - minimal

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "Minimal context"
```

```bash
certo status x-abc1234
```

**Expected**

```
x-abc1234: Minimal context
```

**Not Expected**

```
Expires:
Modifications:
```

## Missing claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo status c-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Missing issue

```toml
[spec]
name = "test"
version = 1
```

```bash
certo status i-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Missing context

```toml
[spec]
name = "test"
version = 1
```

```bash
certo status x-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Unknown ID prefix

```toml
[spec]
name = "test"
version = 1
```

```bash
certo status z-unknown
```

**Exit Code:** 1

**Expected Stderr**

```
unknown
```
