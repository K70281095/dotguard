# Annotation reference

Annotations are comments of the form `# @name value` placed directly above a key in
`.env.example`. Ordinary comments in the same block are kept as documentation. A blank line
ends the block, so an annotation never "leaks" onto an unrelated key.

```bash
# Public base URL of the app.     <- documentation
# @type url                       <- annotation
# @required                       <- annotation
BASE_URL=https://localhost:3000
```

The value written in `.env.example` is only an example; it is not checked.

## `@type`

| Type | Accepts | Rejects |
|---|---|---|
| `string` (default), `str` | anything | — |
| `int`, `integer` | `0`, `-12`, `8080` | `1.5`, `ten` |
| `float`, `number` | `1`, `0.25`, `-3e2` | `abc` |
| `bool`, `boolean` | `true/false`, `yes/no`, `on/off`, `1/0` (any case) | `maybe` |
| `port` | integers `1`–`65535` | `0`, `70000` |
| `url` | values with a scheme and host, e.g. `https://x.io`, `postgres://u@h/db` | `example.com` |
| `email` | `name@domain.tld` | `name@` |

An unknown type is reported as `DG010` on the example file.

## `@required`

The key must have a non-empty value. Without `@required`, an empty value is accepted and no
other rule is applied to it.

## `@optional`

The key may be missing from `.env` entirely. Without `@optional`, every key documented in the
example must be present (rule `DG001`).

`@optional` and `@required` can be combined: "you don't have to set this, but if you do, it
can't be empty".

## `@pattern REGEX`

The value must **fully** match the Python regular expression (`re.fullmatch`).

```bash
# @pattern [a-z0-9-]+\.example\.com
API_HOST=api.example.com
```

## `@values a, b, c`

The value must be exactly one of the comma-separated choices. Whitespace around each choice is
ignored.

## `@min N` and `@max N`

Inclusive numeric bounds. They apply only when `@type` is `int`, `float` or `port`.

## `@secret`

- The value is printed as `****` in every message.
- `dotguard scan` treats the key as sensitive whatever its name.
- `dotguard init` never copies its value.

dotguard already treats names containing `SECRET`, `TOKEN`, `PASSWORD`, `PRIVATE`,
`CREDENTIAL`, `API_KEY`, `ACCESS_KEY` or `AUTH` as sensitive when scanning.

## `@deprecated [reason]`

Warns (`DG008`) when the key is still set in `.env`. Usually combined with `@optional`, so that
removing the key does not trigger `DG001`.

```bash
# @deprecated use LOG_LEVEL=debug instead
# @optional
VERBOSE=
```
