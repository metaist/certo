# status - Timestamps

## Claim with timestamps

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"
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
