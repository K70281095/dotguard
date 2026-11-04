# Rule codes

Each problem dotguard reports has a stable code. Codes never change meaning, so it is safe to
filter on them in scripts and CI.

## `check` rules

| Code | Severity | Meaning | How to fix |
|---|---|---|---|
| `DG001` | error | A key documented in the example is missing from `.env`. | Add it, or mark it `@optional`. |
| `DG002` | warning (error with `--strict`) | `.env` contains a key that the example does not document. | Document it in the example, or remove it. |
| `DG003` | error | A `@required` key is empty. | Give it a value. |
| `DG004` | error | The value does not match its `@type`. | Fix the value, or the type. |
| `DG005` | error | The value does not fully match `@pattern`. | Fix the value, or the pattern. |
| `DG006` | error | A numeric value is below `@min` or above `@max`. | Bring it into range. |
| `DG007` | error | The value is not one of `@values`. | Use one of the listed choices. |
| `DG008` | warning | A `@deprecated` key is still set. | Migrate to the replacement and remove it. |
| `DG009` | warning | Unknown annotation (often a typo such as `@requird`). | Fix the spelling. |
| `DG010` | error | Invalid annotation: unknown `@type`, or a `@pattern` that is not a valid regex. | Fix the example file. |

## `scan` rules

| Code | Severity | Meaning |
|---|---|---|
| `DS001` | error | The value matches a well-known credential format (AWS, GitHub, Slack, Stripe live, Google, OpenAI-style, PEM private key, JWT). |
| `DS002` | warning | A long, high-entropy value under a sensitive-looking name or a `@secret` key. |

If `DS001` fires on a file you already committed, **rotate the credential**: removing it from
the file does not remove it from git history.

## Parse errors (exit code 2)

These stop the run instead of being reported as issues:

- `expected KEY=value`
- `invalid key 'NAME'` (keys must start with a letter or `_` and contain only letters, digits,
  `_` and `.`)
- `unterminated quoted value`
- `unexpected text after closing quote`
- `duplicate key 'NAME'`
