# certo check --only and --skip

## Skip a claim by ID

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-skip-me"
text = "This should be skipped"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "exit 1"

[[claims]]
id = "c-run-me"
text = "This should run"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo hello"
```

```bash
certo check --skip c-skip-me
```

**Expected**

```
✓
Passed: 1
```

**Not Expected**

```
c-skip-me
```

## Run only specific claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-only-this"
text = "Only run this"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo hello"

[[claims]]
id = "c-not-this"
text = "Do not run this"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "exit 1"
```

```bash
certo check --only c-only-this
```

**Expected**

```
✓
c-only-this
Passed: 1
```

**Not Expected**

```
c-not-this
```

## Skip multiple claims

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-one"
text = "Claim one"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "exit 1"

[[claims]]
id = "c-two"
text = "Claim two"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "exit 1"

[[claims]]
id = "c-three"
text = "Claim three"
status = "confirmed"

[[claims.checks]]
kind = "shell"
cmd = "echo ok"
```

```bash
certo check --skip c-one,c-two
```

**Expected**

```
✓
c-three
Passed: 1
```

**Not Expected**

```
c-one
c-two
```

## Check verbose shows skipped checks

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
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

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-test"
kind = "shell"
cmd = "true"

[[claims]]
id = "c-fail"
text = "Failing claim"
status = "confirmed"

[[claims.checks]]
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

## Check with skipped claim shows reason in verbose

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"
level = "skip"

[[claims.checks]]
id = "k-test"
kind = "shell"
cmd = "false"
```

```bash
certo check -v
```

**Expected**

```
⊘
level=skip
```

## Check json format

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
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

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
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

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
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

## Check with skipped check not verbose

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-disabled"
kind = "shell"
status = "disabled"
cmd = "echo hello"

[[claims.checks]]
id = "k-enabled"
kind = "shell"
cmd = "true"
```

```bash
certo check
```

**Expected**

```
✓ [c-test] Test claim
  ✓ k-enabled [shell]
Passed: 1
```
