# status - Filter Tests

## Show only claims with --claims

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
```

```bash
certo status --claims
```

**Expected**

```
Claims:
  c-abc1234  Test claim
```

**Not Expected**

```
Issues:
```

## Show only checks with --checks

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"

[[probes]]
id = "k-abc1234"
kind = "shell"
cmd = "echo test"
```

```bash
certo status --checks
```

**Expected**

```
Checks:
  ● [k-abc1234] shell
```

**Not Expected**

```
Claims:
```
