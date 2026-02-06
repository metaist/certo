# certo check commands

## List checks

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-one"
kind = "shell"
cmd = "echo hello"

[[checks]]
id = "k-two"
kind = "fact"
has = "python.version"
```

```bash
certo check list
```

**Expected**

```
k-one  [shell]
k-two  [fact]
```

## List checks empty

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check list
```

**Expected**

```
No checks found
```

## List checks filtered by kind

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-shell"
kind = "shell"
cmd = "echo hello"

[[checks]]
id = "k-fact"
kind = "fact"
has = "python.version"
```

```bash
certo check list --kind shell
```

**Expected**

```
k-shell  [shell]
```

**Not Expected**

```
k-fact
```

## List checks filtered by status

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-enabled"
kind = "shell"
cmd = "echo hello"

[[checks]]
id = "k-disabled"
kind = "shell"
status = "disabled"
cmd = "echo world"
```

```bash
certo check list --status enabled
```

**Expected**

```
k-enabled  [shell]
```

**Not Expected**

```
k-disabled
```

## Show check detail

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check show k-test
```

**Expected**

```
ID:     k-test
Kind:   shell
Status: enabled
Cmd:    echo hello
```

## Show check not found

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check show k-missing
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Add shell check

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add shell --cmd "echo test"
```

**Expected**

```
Added check:
```

## Add shell check with ID

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add shell --id k-custom --cmd "echo test"
```

**Expected**

```
Added check: k-custom
```

## Add shell check missing cmd

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add shell
```

**Exit Code:** 1

**Expected Stderr**

```
require --cmd
```

## Add fact check with has

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add fact --has python.version
```

**Expected**

```
Added check:
```

## Add fact check missing option

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add fact
```

**Exit Code:** 1

**Expected Stderr**

```
require
```

## Add LLM check

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add llm --files README.md --prompt "Check it"
```

**Expected**

```
Added check:
```

## Add LLM check missing files

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add llm
```

**Exit Code:** 1

**Expected Stderr**

```
require --files
```

## Add URL check

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add url --url https://example.com
```

**Expected**

```
Added check:
```

## Add URL check missing url

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add url
```

**Exit Code:** 1

**Expected Stderr**

```
require --url
```

## Remove check

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-remove-me"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check remove k-remove-me
```

**Expected**

```
Removed check: k-remove-me
```

## Remove check not found

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check remove k-missing
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

[[checks]]
id = "k-test"
kind = "shell"
status = "disabled"
cmd = "echo hello"
```

```bash
certo check on k-test
```

**Expected**

```
Enabled check: k-test
```

## Enable already enabled check

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check on k-test
```

**Expected**

```
already enabled
```

## Disable check

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check off k-test
```

**Expected**

```
Disabled check: k-test
```

## Disable already disabled check

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
status = "disabled"
cmd = "echo hello"
```

```bash
certo check off k-test
```

**Expected**

```
already disabled
```

## Check run subcommand

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check run
```

**Expected**

```
✓ k-test
Passed: 1
```

## Check list no spec

```bash
certo check list
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## Check show no spec

```bash
certo check show k-test
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## Check add no spec

```bash
certo check add shell --cmd "echo test"
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## Check remove no spec

```bash
certo check remove k-test
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## Check on no spec

```bash
certo check on k-test
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## Check off no spec

```bash
certo check off k-test
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## Show LLM check detail

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-llm"
kind = "llm"
files = ["README.md"]
prompt = "Check this"
```

```bash
certo check show k-llm
```

**Expected**

```
ID:     k-llm
Kind:   llm
Files:  ['README.md']
Prompt: Check this
```

## Show fact check detail

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-fact"
kind = "fact"
has = "python.version"
```

```bash
certo check show k-fact
```

**Expected**

```
ID:     k-fact
Kind:   fact
Has:    python.version
```

## Show URL check detail

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-url"
kind = "url"
url = "https://example.com"
cmd = "jq ."
```

```bash
certo check show k-url
```

**Expected**

```
ID:     k-url
Kind:   url
URL:    https://example.com
Cmd:    jq .
```

## Show check JSON format

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check show k-test --format json
```

**Expected**

```
"id": "k-test"
"kind": "shell"
"cmd": "echo hello"
```

## List checks JSON format

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check list --format json
```

**Expected**

```
"checks"
"id": "k-test"
```

## Add check duplicate ID

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-exists"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check add shell --id k-exists --cmd "echo world"
```

**Exit Code:** 1

**Expected Stderr**

```
already exists
```

## Add fact check with equals

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add fact --equals python.version --value "3.14"
```

**Expected**

```
Added check:
```

## Add fact check equals without value

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add fact --equals python.version
```

**Exit Code:** 1

**Expected Stderr**

```
--value
```

## Show shell check with exit code

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "grep pattern"
exit_code = 1
matches = ["found"]
timeout = 30
```

```bash
certo check show k-test
```

**Expected**

```
ID:     k-test
Kind:   shell
Cmd:    grep pattern
Exit:   1
Match:  ['found']
Timeout: 30s
```

## Show fact check with empty

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-fact"
kind = "fact"
empty = "python.issues"
```

```bash
certo check show k-fact
```

**Expected**

```
ID:     k-fact
Kind:   fact
Empty:  python.issues
```

## Show fact check with equals

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-fact"
kind = "fact"
equals = "python.version"
value = "3.14"
```

```bash
certo check show k-fact
```

**Expected**

```
ID:     k-fact
Kind:   fact
Equals: python.version = 3.14
```

## Enable check not found

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check on k-missing
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Disable check not found

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check off k-missing
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## List checks quiet mode

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check list -q
```

**Not Expected**

```
k-test
```

## Show check quiet mode

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-test"
kind = "shell"
cmd = "echo hello"
```

```bash
certo check show k-test -q
```

**Not Expected**

```
ID:
```

## List checks with disabled

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-disabled"
kind = "shell"
status = "disabled"
cmd = "echo hello"
```

```bash
certo check list
```

**Expected**

```
k-disabled  [shell] [disabled]
```

## Add shell check with matches

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add shell --cmd "echo hello" --matches "hello,world"
```

**Expected**

```
Added check:
```

## Add URL check with cmd

```toml
[spec]
name = "test"
version = 1
```

```bash
certo check add url --url https://example.com --cmd "jq ."
```

**Expected**

```
Added check:
```
