# CVE-2022-4963 – FOLIO Spring Module Core SQL Injection PoC

This Proof-of-Concept shows how an attacker can abuse the missing
validation in `HibernateSchemaService` / `SchemaService` of FOLIO **spring-module-core**
(< 2.0.0) to smuggle arbitrary SQL statements through the *schema name*.

The fix ([commit `d374a5f`][GH-patch]) tightens the implementation by

1. validating the schema  name against the regular expression
   `[a-zA-Z0-9_]+` (see `SchemaService.getSchema`) and
2. switching from plain `Statement` to `PreparedStatement` for
   `schemaExists`.

Older versions are still vulnerable and allow payloads such as

```
eviltenant; DROP TABLE users; --
```

which will be interpolated verbatim into statements like

```
DROP SCHEMA IF EXISTS eviltenant; DROP TABLE users; -- CASCADE
```

The PoC below demonstrates that **no exception is raised** and the
payload passes through the API untouched.

---

## Quick Start

```bash
./run_poc.sh
```

Expected output (vulnerable build):

```
=== CVE-2022-4963 FOLIO spring-module-core PoC ===
[VULN] Generated schema name contains SQL metacharacters:
       eviltenant; DROP TABLE users; --_spring_module_core
```

If the library has been patched you will instead see a
`[SAFE]` message reporting that the malicious tenant name has been
rejected.

---

## References

* GitHub Advisory: <https://github.com/advisories/GHSA-4h5h-p23f-hjqf>
* Fix commit: <https://github.com/folio-org/spring-module-core/commit/d374a5f77e6b58e36f0e0e4419be18b95edcd7ff>

[GH-patch]: https://github.com/folio-org/spring-module-core/commit/d374a5f77e6b58e36f0e0e4419be18b95edcd7ff 