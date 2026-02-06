# certo claim check

## Show claim check help

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim check
```

**Expected**

```
usage:
```

## Add shell check

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim check add c-test shell --cmd "echo hello"
```

**Expected**

```
Added check:
```

## Add shell check missing cmd

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim check add c-test shell
```

**Exit Code:** 1

**Expected Stderr**

```
--cmd is required
```

## Add llm check

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim check add c-test llm --files "README.md"
```

**Expected**

```
Added check:
```

## Add llm check missing files

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim check add c-test llm
```

**Exit Code:** 1

**Expected Stderr**

```
--files is required
```

## Add fact check with has

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim check add c-test fact --has "uses.uv"
```

**Expected**

```
Added check:
```

## Add fact check missing criteria

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim check add c-test fact
```

**Exit Code:** 1

**Expected Stderr**

```
--has, --empty, --equals, or --fact-matches is required
```

## Add check to missing claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim check add c-notfound shell --cmd "echo"
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## List checks empty

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim check list c-test
```

**Expected**

```
No checks defined
```

## List checks

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "shell"
id = "k-abc123"
cmd = "echo hello"
```

```bash
certo claim check list c-test
```

**Expected**

```
k-abc123
shell
```

## View check

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "shell"
id = "k-abc123"
cmd = "echo hello"
```

```bash
certo claim check view k-abc123
```

**Expected**

```
ID:      k-abc123
Kind:    shell
Status:  enabled
Claim:   c-test
Command: echo hello
```

## View check not found

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim check view k-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Enable check

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "shell"
id = "k-abc123"
status = "disabled"
cmd = "echo hello"
```

```bash
certo claim check on k-abc123
```

**Expected**

```
Enabled: k-abc123
```

## Disable check

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
kind = "shell"
id = "k-abc123"
status = "enabled"
cmd = "echo hello"
```

```bash
certo claim check off k-abc123
```

**Expected**

```
Disabled: k-abc123
```
