# certo claim

## Create a claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim "Test claim"
```

**Expected**

```
Created claim:
```

## Create a claim with options

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim "Test claim" --level block --tags foo,bar --why "Because reasons"
```

**Expected**

```
Created claim:
```

## Create claim with no spec

```bash
certo claim "Test claim"
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Create claim without text

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim
```

**Exit Code:** 1

**Expected Stderr**

```
required
```

## Create duplicate claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-8ba75d3"
text = "Test claim"
```

```bash
certo claim "Test claim"
```

**Exit Code:** 1

**Expected Stderr**

```
already exists
```

## Confirm a claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-8ba75d3"
text = "Test claim"
status = "pending"
```

```bash
certo claim --confirm c-8ba75d3
```

**Expected**

```
Confirmed: c-8ba75d3
```

## Confirm already confirmed claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-8ba75d3"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim --confirm c-8ba75d3
```

**Expected**

```
already confirmed
```

## Confirm non-existent claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim --confirm c-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Reject a claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-8ba75d3"
text = "Test claim"
status = "pending"
```

```bash
certo claim --reject c-8ba75d3
```

**Expected**

```
Rejected: c-8ba75d3
```

## Reject already rejected claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-8ba75d3"
text = "Test claim"
status = "rejected"
```

```bash
certo claim --reject c-8ba75d3
```

**Expected**

```
already rejected
```

## Reject non-existent claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim --reject c-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Create claim with JSON output

```toml
[spec]
name = "test"
version = 1
```

```bash
certo --format json claim "Test claim"
```

**Expected**

```
"id":
"text": "Test claim"
```
