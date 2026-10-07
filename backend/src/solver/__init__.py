"""io1-solver backend - exact simplex engine with per-method adapters.

Architecture (approved by the course professor):
- engine/  : one generic, method-agnostic simplex solver (exact arithmetic:
  fractions.Fraction plus a symbolic M coefficient).
- methods/ : per-method builders (construct the initial tableau) and
  interpreters (turn EngineResult into a human-readable report).
- The engine never knows which method is running; a method never
  re-implements pivoting. The single source of truth for every signature
  is docs/contracts.md.
"""
