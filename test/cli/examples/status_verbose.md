# status - Verbose Mode

## Verbose claims with tags and author

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"
author = "metaist"
tags = ["testing", "core"]
created = 2026-02-05T12:00:00Z
```

```bash
certo -v status --claims
```

**Expected**

```
Claims:
  c-abc1234  Test claim
        Tags: testing, core
        By metaist
```

## Verbose claims without tags

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
author = "tester"
created = 2026-02-05T12:00:00Z
```

```bash
certo -v status --claims
```

**Expected**

```
  c-abc1234  Test claim
        By tester
```

**Not Expected**

```
Tags:
```

## Verbose claims without author

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
```

```bash
certo -v status --claims
```

**Expected**

```
  c-abc1234  Test claim
```

**Not Expected**

```
By
```

## Verbose claims with author but no date

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
author = "tester"
```

```bash
certo -v status --claims
```

**Expected**

```
  c-abc1234  Test claim
        By tester
```

## Verbose issues with tags

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Test issue"
status = "closed"
tags = ["architecture"]
closed_reason = "Resolved"
```

```bash
certo -v status --issues
```

**Expected**

```
Issues:
  i-abc1234  Test issue [closed]
        Tags: architecture
        Reason: Resolved
```

## Verbose issues without tags or reason

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Test issue"
```

```bash
certo -v status --issues
```

**Expected**

```
  i-abc1234  Test issue
```

**Not Expected**

```
Tags:
Reason:
```

## Verbose contexts with description and expiration

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "Test context"
description = "A test context description"
expires = 2026-12-31T00:00:00Z
```

```bash
certo -v status --contexts
```

**Expected**

```
Contexts:
  x-abc1234  Test context
        A test context description
        Expires: 2026-12-31
```

## Verbose contexts truncates long descriptions

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "Test context"
description = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
```

```bash
certo -v status --contexts
```

**Expected**

```
...
```

## Verbose contexts without description or expiration

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "Test context"
```

```bash
certo -v status --contexts
```

**Expected**

```
  x-abc1234  Test context
```

**Not Expected**

```
Expires:
```
