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

## Add url check

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
certo claim check add c-test url --url "https://example.com"
```

**Expected**

```
Added check:
```

## Add url check missing url

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
certo claim check add c-test url
```

**Exit Code:** 1

**Expected Stderr**

```
--url is required
```

## View llm check

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-llm123"
kind = "llm"
files = ["README.md"]
```

```bash
certo claim check view k-llm123
```

**Expected**

```
ID:      k-llm123
Kind:    llm
Status:  enabled
Claim:   c-test
Files:   ['README.md']
```

## View fact check

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-fact123"
kind = "fact"
has = "uses.uv"
```

```bash
certo claim check view k-fact123
```

**Expected**

```
ID:      k-fact123
Kind:    fact
Status:  enabled
Claim:   c-test
Has:     uses.uv
```

## View url check

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-url123"
kind = "url"
url = "https://example.com"
cmd = "cat"
```

```bash
certo claim check view k-url123
```

**Expected**

```
ID:      k-url123
Kind:    url
Status:  enabled
Claim:   c-test
URL:     https://example.com
Command: cat
```

## Add fact check with empty

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
certo claim check add c-test fact --empty "python.consistency-issues"
```

**Expected**

```
Added check:
```

## Check already enabled

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-abc123"
kind = "shell"
status = "enabled"
cmd = "echo hello"
```

```bash
certo claim check on k-abc123
```

**Expected**

```
already enabled
```

## Check already disabled

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-abc123"
kind = "shell"
status = "disabled"
cmd = "echo hello"
```

```bash
certo claim check off k-abc123
```

**Expected**

```
already disabled
```

## List checks on missing claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo claim check list c-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## View shell check with all options

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-shell123"
kind = "shell"
cmd = "echo test"
exit_code = 1
matches = ["pattern"]
not_matches = ["bad"]
timeout = 30
```

```bash
certo claim check view k-shell123
```

**Expected**

```
ID:      k-shell123
Kind:    shell
Status:  enabled
Claim:   c-test
Command: echo test
Exit:    1
Matches: ['pattern']
Not:     ['bad']
Timeout: 30s
```

## View url check with all options

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-url123"
kind = "url"
url = "https://example.com"
cache_ttl = 3600
cmd = "jq ."
exit_code = 1
matches = ["ok"]
not_matches = ["error"]
timeout = 30
```

```bash
certo claim check view k-url123
```

**Expected**

```
ID:      k-url123
Kind:    url
Status:  enabled
Claim:   c-test
URL:     https://example.com
TTL:     3600s
Command: jq .
Exit:    1
Matches: ['ok']
Not:     ['error']
Timeout: 30s
```

## View llm check with prompt

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-llm123"
kind = "llm"
files = ["README.md"]
prompt = "Check the readme"
```

```bash
certo claim check view k-llm123
```

**Expected**

```
ID:      k-llm123
Kind:    llm
Status:  enabled
Claim:   c-test
Files:   ['README.md']
Prompt:  Check the readme
```

## View fact check with equals

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-fact123"
kind = "fact"
equals = "python.min-version"
value = "3.11"
```

```bash
certo claim check view k-fact123
```

**Expected**

```
ID:      k-fact123
Kind:    fact
Status:  enabled
Claim:   c-test
Equals:  python.min-version
Value:   3.11
```

## View fact check with matches

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-fact123"
kind = "fact"
matches = "python.requires-python"
pattern = ">=3\\.11"
```

```bash
certo claim check view k-fact123
```

**Expected**

```
ID:      k-fact123
Kind:    fact
Status:  enabled
Claim:   c-test
Matches: python.requires-python
Pattern: >=3\.11
```

## Check add without spec

```bash
certo claim check add c-test shell --cmd "true"
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## Check list without spec

```bash
certo claim check list c-test
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## Check view without spec

```bash
certo claim check view k-test
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## Check on without spec

```bash
certo claim check on k-test
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## Check off without spec

```bash
certo claim check off k-test
```

**Exit Code:** 1

**Expected Stderr**

```
No spec found
```

## View check not found

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
certo claim check view k-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Enable check not found

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
certo claim check on k-notfound
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

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"
```

```bash
certo claim check off k-notfound
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
certo claim check list c-test -q
```

**Expected**

```

```

## View check quiet mode

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
certo claim check view k-test -q
```

**Expected**

```

```

## View url check without command

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-url123"
kind = "url"
url = "https://example.com"
```

```bash
certo claim check view k-url123
```

**Expected**

```
ID:      k-url123
Kind:    url
Status:  enabled
Claim:   c-test
URL:     https://example.com
```

## View fact check with empty criterion

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-test"
text = "Test claim"
status = "confirmed"

[[claims.checks]]
id = "k-fact123"
kind = "fact"
empty = "python.issues"
```

```bash
certo claim check view k-fact123
```

**Expected**

```
ID:      k-fact123
Kind:    fact
Status:  enabled
Claim:   c-test
```
