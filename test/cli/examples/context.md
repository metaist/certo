# certo context

## Create a context

```toml
[spec]
name = "test"
version = 1
```

```bash
certo context "release"
```

**Expected**

```
Created context:
```

## Create a context with description

```toml
[spec]
name = "test"
version = 1
```

```bash
certo context "release" --description "For release builds"
```

**Expected**

```
Created context:
```

## Create context with no spec

```bash
certo context "release"
```

**Exit Code:** 1

**Expected Stderr**

```
no spec
```

## Create context without name

```toml
[spec]
name = "test"
version = 1
```

```bash
certo context
```

**Exit Code:** 1

**Expected Stderr**

```
required
```

## Create duplicate context

```toml
[spec]
name = "test"
version = 1

[[contexts]]
id = "x-a4d451e"
name = "release"
```

```bash
certo context "release"
```

**Exit Code:** 1

**Expected Stderr**

```
already exists
```

## Create context with JSON output

```toml
[spec]
name = "test"
version = 1
```

```bash
certo --format json context "release"
```

**Expected**

```
"id":
"name": "release"
```
