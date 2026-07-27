# Safe refactor

Refactor only the targeted script(s) without changing CLI behavior.

Guardrails:
- Do not alter usage strings unless explicitly requested
- Keep output wording stable unless fixing a bug
- Preserve silent-by-default behavior
- Preserve stderr error paths and exit codes
- Avoid adding cross-tool shared modules

Deliverables:
- Minimal diffs
- Updated tests if behavior changed
- README updates only if user-facing behavior changed
