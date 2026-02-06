# certo issue

## Create an issue

```toml
[spec]
name = "test"
version = 1
```

```bash
certo issue "Should we do this?"
```

**Expected**

```
Created issue:
```

## Create an issue with tags

```toml
[spec]
name = "test"
version = 1
```

```bash
certo issue "Question?" --tags arch,design
```

**Expected**

```
Created issue:
```

## Create issue with no spec

```bash
certo issue "Question?"
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Create issue without text

```toml
[spec]
name = "test"
version = 1
```

```bash
certo issue
```

**Exit Code:** 1

**Expected Stderr**

```
required
```

## Create duplicate issue

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-ff0cda1"
text = "Question?"
```

```bash
certo issue "Question?"
```

**Exit Code:** 1

**Expected Stderr**

```
already exists
```

## Close an issue

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-ff0cda1"
text = "Question?"
status = "open"
```

```bash
certo issue --close i-ff0cda1
```

**Expected**

```
Closed: i-ff0cda1
```

## Close an issue with reason

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-ff0cda1"
text = "Question?"
status = "open"
```

```bash
certo issue --close i-ff0cda1 --reason "Decided to do X"
```

**Expected**

```
Closed: i-ff0cda1
```

## Close already closed issue

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-ff0cda1"
text = "Question?"
status = "closed"
```

```bash
certo issue --close i-ff0cda1
```

**Expected**

```
already closed
```

## Close non-existent issue

```toml
[spec]
name = "test"
version = 1
```

```bash
certo issue --close i-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Reopen an issue

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-ff0cda1"
text = "Question?"
status = "closed"
```

```bash
certo issue --reopen i-ff0cda1
```

**Expected**

```
Reopened: i-ff0cda1
```

## Reopen already open issue

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-ff0cda1"
text = "Question?"
status = "open"
```

```bash
certo issue --reopen i-ff0cda1
```

**Expected**

```
already open
```

## Reopen non-existent issue

```toml
[spec]
name = "test"
version = 1
```

```bash
certo issue --reopen i-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Create issue with JSON output

```toml
[spec]
name = "test"
version = 1
```

```bash
certo --format json issue "Question?"
```

**Expected**

```
"id":
"text": "Question?"
```
