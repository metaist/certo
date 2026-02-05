# spec show - Basic Tests

## Show claims and issues

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"

[[issues]]
id = "i-abc1234"
text = "Test issue"
```

```bash
certo spec show
```

**Expected**

```
Claims:
  c-abc1234  Test claim
Issues:
  i-abc1234  Test issue
```

## Show empty spec

```toml
[spec]
name = "test"
version = 1
```

```bash
certo spec show
```

**Not Expected**

```
Claims:
Issues:
Contexts:
```

## Missing spec file

```bash
certo spec show
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```
