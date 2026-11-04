# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Use GitHub's private vulnerability reporting instead:
**Security → Report a vulnerability** on the
[repository page](https://github.com/K70281095/dotguard/security/advisories/new).

Please include:

- what you found and why it is a security issue,
- steps or a minimal example to reproduce it (with fake values only),
- the dotguard version and Python version you used.

You can expect an acknowledgement within 7 days. Once a fix is ready, we will publish a release
and credit you in the advisory unless you prefer to stay anonymous.

## Scope

Examples of issues we especially want to hear about:

- dotguard printing, logging or writing a value that is marked `@secret` or looks sensitive,
- `dotguard init` copying a secret into the generated `.env.example`,
- a crafted `.env` file causing excessive CPU or memory use.

Note that `dotguard scan` is a safety net, not a guarantee: it cannot detect every possible
credential format. Use it alongside your platform's secret scanning.
