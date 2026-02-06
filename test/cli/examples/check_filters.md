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
Passed: 2
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
Passed: 2
```

**Not Expected**

```
c-one
c-two
```
