# certo issue

## Create an issue

```toml
[spec]
name = "test"
version = 1
```

```bash
certo issue add "Should we do this?"
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
certo issue add "Question?" --tags arch,design
```

**Expected**

```
Created issue:
```

## Create issue with no spec

```bash
certo issue add "Question?"
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
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
certo issue add "Question?"
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
certo issue close i-ff0cda1
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
certo issue close i-ff0cda1 --reason "Decided to do X"
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
certo issue close i-ff0cda1
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
certo issue close i-notfound
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
certo issue reopen i-ff0cda1
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
certo issue reopen i-ff0cda1
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
certo issue reopen i-notfound
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
certo --format json issue add "Question?"
```

**Expected**

```
"id":
"text": "Question?"
```

## List issues

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "First issue"
status = "open"

[[issues]]
id = "i-def5678"
text = "Second issue"
status = "closed"
```

```bash
certo issue list
```

**Expected**

```
i-abc1234
i-def5678
```

## List issues filtered by status

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "First issue"
status = "open"

[[issues]]
id = "i-def5678"
text = "Second issue"
status = "closed"
```

```bash
certo issue list --status open
```

**Expected**

```
i-abc1234
```

**Not Expected**

```
i-def5678
```

## View an issue

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Test issue"
status = "open"
```

```bash
certo issue view i-abc1234
```

**Expected**

```
ID:      i-abc1234
Text:    Test issue
Status:  open
```

## View non-existent issue

```toml
[spec]
name = "test"
version = 1
```

```bash
certo issue view i-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Show issue help

```toml
[spec]
name = "test"
version = 1
```

```bash
certo issue
```

**Expected**

```
usage:
```

## List issues empty

```toml
[spec]
name = "test"
version = 1
```

```bash
certo issue list
```

**Expected**

```
No issues found
```

## List issues no spec

```bash
certo issue list
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## View issue no spec

```bash
certo issue view i-xxx
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Close issue no spec

```bash
certo issue close i-xxx
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Reopen issue no spec

```bash
certo issue reopen i-xxx
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## List issues quiet mode

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Test issue"
status = "open"
```

```bash
certo issue list -q
```

**Not Expected**

```
i-abc1234
```

## View issue quiet mode

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Test issue"
status = "open"
```

```bash
certo issue view i-abc1234 -q
```

**Not Expected**

```
ID:
```

## View issue with all fields

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Test issue"
status = "closed"
tags = ["question", "design"]
closed_reason = "Decided to do X"
created = 2024-01-01T00:00:00Z
updated = 2024-01-02T00:00:00Z
```

```bash
certo issue view i-abc1234
```

**Expected**

```
ID:      i-abc1234
Text:    Test issue
Status:  closed
Tags:    question, design
Reason:  Decided to do X
Created:
Updated:
```
