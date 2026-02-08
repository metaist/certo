# certo check --only and --skip

## Skip a check by ID

```toml
[spec]
name = "test"
version = 1

[[probes]]
id = "k-skip-me"
kind = "shell"
cmd = "exit 1"

[[probes]]
id = "k-run-me"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check --skip k-skip-me
```

**Expected**

```
✓ k-run-me
Passed: 1
```

**Not Expected**

```
k-skip-me
```

## Run only specific check

```toml
[spec]
name = "test"
version = 1

[[probes]]
id = "k-only-this"
kind = "shell"
cmd = "echo hello"

[[probes]]
id = "k-not-this"
kind = "shell"
cmd = "exit 1"
```

```bash
certo check --only k-only-this
```

**Expected**

```
✓ k-only-this
Passed: 1
```

**Not Expected**

```
k-not-this
```

## Skip multiple checks

```toml
[spec]
name = "test"
version = 1

[[probes]]
id = "k-one"
kind = "shell"
cmd = "exit 1"

[[probes]]
id = "k-two"
kind = "shell"
cmd = "exit 1"

[[probes]]
id = "k-three"
kind = "shell"
cmd = "echo ok"
```

```bash
certo check --skip k-one,k-two
```

**Expected**

```
✓ k-three
Passed: 1
```

**Not Expected**

```
k-one
k-two
```

## Check verbose shows disabled checks

```toml
[spec]
name = "test"
version = 1

[[probes]]
id = "k-disabled"
kind = "shell"
status = "disabled"
cmd = "echo hello"
```

```bash
certo check -v
```

**Expected**

```
k-disabled
disabled
```

## Check quiet hides passed

```toml
[spec]
name = "test"
version = 1

[[probes]]
id = "k-pass"
kind = "shell"
cmd = "true"

[[probes]]
id = "k-fail"
kind = "shell"
cmd = "false"
```

```bash
certo check -q
```

**Exit Code:** 1

**Expected**

```
✗
Failed: 1
```

## Check json format

```toml
[spec]
name = "test"
version = 1

[[probes]]
id = "k-test"
kind = "shell"
cmd = "true"
```

```bash
certo check --format json
```

**Expected**

```
"passed": 1
"failed": 0
```

## Check verbose with failure

```toml
[spec]
name = "test"
version = 1

[[probes]]
id = "k-test"
kind = "shell"
cmd = "false"
```

```bash
certo check -v
```

**Exit Code:** 1

**Expected**

```
k-test [shell] Expected exit code 0, got 1
```

## Check json format with failure

```toml
[spec]
name = "test"
version = 1

[[probes]]
id = "k-test"
kind = "shell"
cmd = "false"
```

```bash
certo check --format json
```

**Exit Code:** 1

**Expected**

```
"passed": 0
"failed": 1
```

## Check with disabled check not verbose

```toml
[spec]
name = "test"
version = 1

[[probes]]
id = "k-disabled"
kind = "shell"
status = "disabled"
cmd = "echo hello"

[[probes]]
id = "k-enabled"
kind = "shell"
cmd = "true"
```

```bash
certo check
```

**Expected**

```
✓ k-enabled
Passed: 1
```
