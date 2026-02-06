# status - Status and Level Markers

## Claim status markers

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-pending"
text = "Pending claim"
status = "pending"

[[claims]]
id = "c-confirmed"
text = "Confirmed claim"
status = "confirmed"

[[claims]]
id = "c-superseded"
text = "Superseded claim"
status = "superseded"

[[claims]]
id = "c-rejected"
text = "Rejected claim"
status = "rejected"
```

```bash
certo status --claims
```

**Expected**

```
  c-pending  Pending claim [pending]
  c-confirmed  Confirmed claim
  c-superseded  Superseded claim [superseded]
  c-rejected  Rejected claim [rejected]
```

## Claim level markers

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-warn"
text = "Warn claim"
status = "confirmed"
level = "warn"

[[claims]]
id = "c-block"
text = "Block claim"
status = "confirmed"
level = "block"

[[claims]]
id = "c-skip"
text = "Skip claim"
status = "confirmed"
level = "skip"
```

```bash
certo status --claims
```

**Expected**

```
  c-warn  Warn claim
  c-block  Block claim *
  c-skip  Skip claim -
```

## Issue status markers

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-open"
text = "Open issue"
status = "open"

[[issues]]
id = "i-closed"
text = "Closed issue"
status = "closed"
```

```bash
certo status --issues
```

**Expected**

```
  i-open  Open issue
  i-closed  Closed issue [closed]
```

## All sections with separating newlines

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"

[[issues]]
id = "i-abc1234"
text = "Test issue"

[[contexts]]
id = "x-abc1234"
name = "Test context"
```

```bash
certo status
```

**Expected**

```
Claims:
  c-abc1234  Test claim

Issues:
  i-abc1234  Test issue

Contexts:
  x-abc1234  Test context
```
