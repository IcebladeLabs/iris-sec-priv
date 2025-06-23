# CVE-2022-45206 JeecgBoot SQL Injection PoC

Proof of Concept demonstrating SQL injection filter bypass in JeecgBoot ≤ 3.4.3 using URL-encoded TAB characters (`%09`).

## Vulnerability Overview

- **CVE**: CVE-2022-45206
- **Type**: SQL Injection Filter Bypass (CWE-089) 
- **CVSS**: 9.8 (Critical)
- **Affected**: JeecgBoot ≤ 3.4.3

## Root Cause

The `SqlInjectionUtil` blacklist filters check for SQL keywords with spaces (e.g., `"select "`) but don't URL-decode input first. Attackers can bypass using `%09` (TAB) instead of spaces.

**Example:**
- Normal: `"select * from users"` → **BLOCKED**
- Bypass: `"select%09*%09from%09users"` → **ALLOWED**

## Quick Test

```bash
./run_poc.sh
```

## References

- [Fix Commit](https://github.com/jeecgboot/JeecgBoot/commit/f18ced524c9ec13e876bfb74785a1b112cc8b6bb)
- [CVE Details](https://nvd.nist.gov/vuln/detail/CVE-2022-45206)
