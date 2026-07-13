# Security Policy

## Scope

This policy covers the `nrdax-python` **tooling** (library and CLI). It does **not**
cover the security of the systems and protocols catalogued *in* NRDAX - those are
described in the dataset itself and disclosed through NullRabbit's advisory process.

## Reporting a vulnerability in this tool

If you find a security issue in `nrdax-python` (for example, unsafe handling of
downloaded data, a path traversal in cache handling, or a parsing crash on
malicious input), please report it privately:

- Email **security@nullrabbit.ai** with the details, or
- Use GitHub's private "Report a vulnerability" feature on this repository.

Please do not open a public issue for undisclosed vulnerabilities.

Include: affected version, a description, reproduction steps, and impact. We aim to
acknowledge within 3 business days and to provide a remediation timeline after
triage.

## Handling untrusted data

The tool validates data at the read boundary and never executes it. Still, when you
point it at an untrusted source (`--source file:...`, `--source stix:...`, a
third-party feed URL), treat the output as untrusted input to whatever you feed it
into. Loading is lenient by default and collects issues; use `--strict` to fail on
the first problem.

## Supported versions

The latest released minor version receives security fixes. Older versions may be
patched at the maintainers' discretion.
