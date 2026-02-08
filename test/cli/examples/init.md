# certo init

## Initialize new spec

```bash
certo init
```

**Expected**

```
Initialized certo spec
```

## Initialize with custom name

```bash
certo init
```

**Expected**

```
Initialized certo spec
```

## Initialize fails if spec exists

```toml
[spec]

version = 1
```

```bash
certo init
```

**Exit Code:** 1

**Expected Stderr**

```
already exists
```

## Initialize with force overwrites

```toml
[spec]

version = 1
```

```bash
certo init --force
```

**Expected**

```
Initialized certo spec
```

## Initialize with JSON output

```bash
certo --format json init
```

**Expected**

```
certo.toml
"path":
```
