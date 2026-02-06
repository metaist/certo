# status - Verbose Output

## Verbose claims show tags and author

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"
author = "metaist"
tags = ["testing", "example"]
created = 2026-02-05T12:00:00Z
```

```bash
certo status -v
```

**Expected**

```
Claims:
  c-abc1234  Test claim
        Tags: testing, example
        By metaist 2026-02-05
```

## Verbose issues show closed reason

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
```

```bash
certo status -v --issues
```

**Expected**

```
Issues:
  i-abc1234  Test issue [closed]
        Tags: architecture
        Reason: Resolved by c-xxx
```
