# Test design for a template import — which technique answers which column

Name the technique per dimension, so a reviewer can see why a value got one row and not five.

| technique | where it applies | gives |
|---|---|---|
| **Decision table** | the importer's lookup of allowed combinations (e.g. movement × tax right × form type in a pairing table) | each valid triple = one happy row · each dead or cross triple = one negative row |
| **Equivalence partitioning** | values that hit the same code path (transport aliases, product families, tenants) | one representative per class, not every value in the dropdown |
| **Boundary values** | quantity (blank · `0` · `-1` fail · `0.001` · `1,234.5` with comma pass) · optional groups that must be all-or-nothing · required header cells blank | stage-2 cases, **one file each** |
| **State transition** | validate → submit → same receipt again | a re-submit must be refused; "validate accepts an already-imported receipt" is a finding |
| **Pairwise** | only when a cross product will not fit — e.g. transport × movement × product family | every *pair* of values once, instead of every triple |

The decision table is exhaustive when it is small; pairwise is for the dimensions outside it.
Read the expected error text off the importer's source (or the adapter's `check()`), never
paraphrase it — `compare()` matches substrings.

## Building the decision table from the database

1. Pull the dropdown lists from the template's hidden master sheet (`_Master` or similar).
2. Pull the allowed-pairs table from the test database (the same table the importer's
   `isAllowed…()` reads). Say which commit of the importer and which date of the table.
3. Cross them: for each movement × dropdown value, list the form types that pass. Three lists fall
   out of it and go first in the report:
   - dropdown values that **never** pass (dead values — a tester keys them and is always refused);
   - pairs that pass in the table but are **missing from the dropdown** (operators cannot key them);
   - pairs the table refuses but **real documents already carry** (keyed via another path — the
     web form and the importer use different rules, tell the dev team).

## Collapsing the negatives into equivalence classes

Every pair outside the valid set is a negative, but the importer decides them all with one lookup,
so one representative per class is enough:

| class | representative |
|---|---|
| X1 a dropdown value with no pair at all | one row per such value |
| X2 a form type with no pair at all | one row |
| X3 a one-direction value used in the wrong direction | one row per direction |
| X4 right direction, but the form belongs to another right | one row |
| X5 stage-2 failure (quantity 0 / blank) | one row, **its own file** — stage 3 never runs behind it |
| X6 a header value copied from another sheet that the alias list does not resolve | one row |

## Dimensions outside the table

The rules above usually do not depend on transport or product, so do not multiply by them —
spread them instead: every transport value, every product family, every slide / use case of the
spec appears at least once in a passing file. Multi-group documents (several rights in one file)
check that details group correctly.

## Keying matrix for manual testers

When testers key the cases by hand, the same design lives in a sheet tab:

- **Key ID** `K<X>-NNN` per transport / scenario family, three-digit, never renumbered or reused —
  defects and results cite it; a dropped case keeps its row.
- Columns: the input dimensions in template order · remark · scenario type (`Happy Case` /
  `Edge Case`) · traceability (which slide / requirement) · evidence link · result · keyed by ·
  expected result.
- **Expected result must be checkable by someone else:** `VALIDATED · 2 details` or the exact
  error string, never "passes" / "works". One rule per row; a row that checks two pairs is two rows.
- Before the run, list every requirement and every dropdown value with **zero** rows — those are
  the gaps, and they go first in the report.
