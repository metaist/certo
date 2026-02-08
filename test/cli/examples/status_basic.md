# status - Basic Tests

## Show empty spec

```toml
[spec]
name = "test"
version = 1
```

```bash
certo status
```

**Not Expected**

```
Claims:
Issues:
Contexts:
```

## Missing spec file

```bash
certo status
```

**Exit Code:** 1

**Expected Stderr**

```
certo.toml
```
