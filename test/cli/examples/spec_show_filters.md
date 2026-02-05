# spec show - Filter Tests

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
certo spec show --claims
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

## Show only issues with --issues

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
certo spec show --issues
```

**Expected**

```
Issues:
  i-abc1234  Test issue
```

**Not Expected**

```
Claims:
```

## Show only contexts with --contexts

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"

[[contexts]]
id = "x-abc1234"
name = "Test context"
```

```bash
certo spec show --contexts
```

**Expected**

```
Contexts:
  x-abc1234  Test context
```

**Not Expected**

```
Claims:
```
