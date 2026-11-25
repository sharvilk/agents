# Lens: Security

Pasted in full into the brief of the reviewer that holds this seat.

## Seat this lens when

The target touches authentication, sessions, tokens, permissions, input from users or other systems, secrets, file or network access, or anything an attacker could call.

## Check

1. Who can call each new entry point, and what stops everyone else? Trace the check to code, not to the plan's word.
2. Where does untrusted input go? Look for queries, shell commands, paths, templates, redirects or deserialisation built from it.
3. Do any secrets or tokens end up in URLs, logs, error messages, analytics, client storage or version control? Check what the logging code actually records.
4. Can a caller learn something they should not from differences in responses or timing (whether an account exists, whether an id is valid)?
5. Are tokens single-use where they should be, do they expire, are they stored hashed, and are they compared in constant time?
6. Is anything rate-limited that an attacker would repeat: logins, resets, codes, sign-ups, expensive calls?
7. Does the plan widen a permission, a role, a network rule or a CORS policy beyond what the asks need?

## Typical blocking-grade findings

- An entry point with no authorisation check.
- A token or secret written where it is logged or shared.
- An enumeration or injection path a normal attacker can reach with a browser or curl.
- A credential stored so that reading the database, a replica or a backup grants access: a plaintext reset or
  session token, password or API key. Read access to stored data is normal (backups, replicas, support tools,
  exports), so this is not speculative hardening.

## Usually not blocking

- Hardening against threats the plan's environment does not have; defence-in-depth extras with no reachable attack.

## Where to look

The authentication and middleware code, the logging setup (what fields it writes), the data model for tokens and sessions, and the repo's security rules.
