# status - JSON Output

## JSON output for claims

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
certo status --format json
```

**Expected**

```
"claims"
"c-abc1234"
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
certo status c-abc1234 --format json
```

**Expected**

```
"id": "c-abc1234"
"status": "confirmed"
```

## JSON output for specific check

```toml
[spec]
name = "test"
version = 1

[[checks]]
id = "k-abc1234"
kind = "shell"
cmd = "echo test"
```

```bash
certo status k-abc1234 --format json
```

**Expected**

```
"id": "k-abc1234"
"kind": "shell"
```
