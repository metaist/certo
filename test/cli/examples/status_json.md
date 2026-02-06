# status - JSON Output

## JSON output for all

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"

[[issues]]
id = "i-abc1234"
text = "Test issue"
```

```bash
certo --format json status
```

**Expected**

```
"claims"
"issues"
"c-abc1234"
"i-abc1234"
```

## JSON output for specific claim

```toml
[spec]
name = "test"
version = 1

[[claims]]
id = "c-abc1234"
text = "Test claim"
status = "confirmed"
```

```bash
certo --format json status c-abc1234
```

**Expected**

```
"id": "c-abc1234"
"text": "Test claim"
"status": "confirmed"
```

## JSON output for specific issue

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
certo --format json status i-abc1234
```

**Expected**

```
"id": "i-abc1234"
"text": "Test issue"
"status": "open"
```

## JSON output for specific context

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-abc1234"
name = "Test context"
description = "A description"
```

```bash
certo --format json status x-abc1234
```

**Expected**

```
"id": "x-abc1234"
"name": "Test context"
"description": "A description"
```
