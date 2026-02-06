# status - Detail Views

## Show claim detail

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"
source = "human"
author = "metaist"
level = "block"
tags = ["testing"]
why = "Because reasons"
considered = ["alt1", "alt2"]
closes = ["i-xxx"]
created = 2026-02-05T12:00:00Z
```

```bash
certo status c-abc1234
```

**Expected**

```
c-abc1234: Test claim
Status: confirmed
Level: block
Author: metaist
Tags: testing
Why: Because reasons
Considered:
  - alt1
  - alt2
Closes: i-xxx
```

## Show claim detail - minimal

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Minimal claim"
```

```bash
certo status c-abc1234
```

**Expected**

```
c-abc1234: Minimal claim
Status: pending
Level: warn
Source: human
```

**Not Expected**

```
Why:
Considered:
Closes:
```

## Show issue detail

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Test issue"
status = "closed"
tags = ["architecture"]
closed_reason = "Resolved by c-xxx"
created = 2026-02-05T12:00:00Z
```

```bash
certo status i-abc1234
```

**Expected**

```
i-abc1234: Test issue
Status: closed
Tags: architecture
Closed reason: Resolved by c-xxx
```

## Show issue detail - minimal

```toml
[spec]
name = "test"
version = 1

[[issues]]
id = "i-abc1234"
text = "Minimal issue"
```

```bash
certo status i-abc1234
```

**Expected**

```
i-abc1234: Minimal issue
Status: open
```

**Not Expected**

```
Tags:
Closed reason:
```

## Show check detail

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-abc1234"
kind = "shell"
cmd = "echo hello"
```

```bash
certo status k-abc1234
```

**Expected**

```
ID:     k-abc1234
Kind:   shell
Status: enabled
Cmd:    echo hello
```

## Missing claim

```toml
[spec]
name = "test"
version = 1
```

```bash
certo status c-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Missing issue

```toml
[spec]
name = "test"
version = 1
```

```bash
certo status i-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Missing check

```toml
[spec]
name = "test"
version = 1
```

```bash
certo status k-notfound
```

**Exit Code:** 1

**Expected Stderr**

```
not found
```

## Unknown ID prefix

```toml
[spec]
name = "test"
version = 1
```

```bash
certo status z-unknown
```

**Exit Code:** 1

**Expected Stderr**

```
unknown
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
cmd = "echo test"
```

```bash
certo status k-url
```

**Expected**

```
ID:     k-url
Kind:   url
Status: enabled
URL:    https://example.com
Cmd:    echo test
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
prompt = "Check it"
```

```bash
certo status k-llm
```

**Expected**

```
ID:     k-llm
Kind:   llm
Files:  ['README.md']
Prompt: Check it
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
certo status k-fact
```

**Expected**

```
ID:     k-fact
Kind:   fact
Has:    python.version
```

## Show shell check with matches

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-shell"
kind = "shell"
cmd = "echo hello"
exit_code = 0
matches = ["hello"]
```

```bash
certo status k-shell
```

**Expected**

```
ID:     k-shell
Kind:   shell
Cmd:    echo hello
Match:  ['hello']
```
