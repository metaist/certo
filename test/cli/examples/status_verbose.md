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
