# status - Status Markers

## Claims show status markers

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-pending"
text = "Pending claim"
status = "pending"

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
Claims:
  c-pending  Pending claim [pending]
  c-superseded  Superseded claim [superseded]
  c-rejected  Rejected claim [rejected]
```

## Claims show level markers

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-block"
text = "Blocking claim"
status = "confirmed"
level = "block"

[[claims]]
id = "c-skip"
text = "Skipped claim"
status = "confirmed"
level = "skip"

[[claims]]
id = "c-warn"
text = "Warning claim"
status = "confirmed"
level = "warn"
```

```bash
certo status --claims
```

**Expected**

```
Claims:
  c-block  Blocking claim *
  c-skip  Skipped claim -
  c-warn  Warning claim
```
