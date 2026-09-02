# NER Model — recovered specification

Source: `NER.xls` (brokerage net-effective-rent calculator, created 2003, last saved 2023; author C. Mansfield). The legacy file's formulas are not directly extractable, so the model was reconstructed from its values and **verified by recomputing every computed cell across all 18 scenarios on both sheets to < 0.0005 $/RSF** (one documented anomaly, below). Reference implementation: [`scripts/ner.py`](../scripts/ner.py).

The workbook has two sheets = two NER flavors sharing one engine:

| Sheet | Inputs | Discounting | Output |
| --- | --- | --- | --- |
| `Net Effective Rent` | bump schedule in **months**, 6%/yr | monthly (rate/12), beginning-of-month toggle | **Average NER annuity** (levelized average rent − levelized concessions) |
| `Ken - Legg` | bump schedule in **years**, 7%/yr | monthly (rate/12), beginning-of-month | **Initial NER** (bump-1 face rent − levelized concessions) |

## The engine

Let `i = annual_rate / 12` (monthly discount rate), `T` = total term in months.

**Annuity factor** (PV of $1/RSF/yr paid monthly, expressed in year-units):

```
AF_end(T) = [(1 − (1+i)^−T) / i] / 12
AF_beg(T) = AF_end(T) × (1+i)          # beginning-of-month convention
```

**1. PV of base rent.** The rent schedule is a sequence of bumps `(rate_b $/RSF/yr, m_b months)` — up to 15 tranches; a tranche may have rate 0 (e.g. a zero-rent stub) and still counts toward the term:

```
PV_end = Σ_b  rate_b × AF_end(m_b) × (1+i)^−t_b      # t_b = months elapsed before bump b
PV_beg = PV_end × (1+i)
```

**2. Levelized base rent** (the "Base Rent annuity"):

```
base = ROUND( PV_beg / AF_beg , 2 )        # ≡ PV_end / AF_end, rounded to cents
```

**3. Concessions — nominal at t = 0, then levelized.** Every concession is converted to a nominal $/RSF figure, treated as if paid upfront (NOT discounted at its actual timing), and levelized by dividing by `AF_beg(T)`:

| Concession | Nominal $/RSF |
| --- | --- |
| Downtime | `downtime_months / 12 × bump1_rate` |
| Free rent | `free_months / 12 × bump1_rate` (valued at the initial rent rate, even if free months span a later bump) |
| TI allowance | as input |
| Additional TI work | as input |
| Commissions | `n_commissions × pct(term_years) × (total_rent − free_rent_nominal) / term_years` |

where `total_rent = Σ_b rate_b × m_b / 12` (nominal $/RSF over the whole term) and `pct(y)` is the **cumulative commission schedule** (e.g. "NY Former": 5% yr 1, 4% yr 2, 3.5% yrs 3–5, … ⇒ cumulative 34% at 11 yrs, 50% at 19 yrs), **linearly interpolated for fractional years** using the next year's incremental rate.

**4. NER:**

```
NER = base − Σ concessions_levelized        # $/RSF/yr annuity over the term
Initial NER (Ken-Legg flavor) = bump1_rate − Σ concessions_levelized
```

## Verified numbers (spot examples)

- Scenario 1 (25,000 RSF, 89×72mo + 96×60mo, 12 mo free, no TI): PV_end 736.47874 → base 91.62 → NER **80.603** ✓
- Scenario 10 ("TBD", 19-yr term, downtime 2 mo, 12 mo free, $60 TI, 1 commission @ 50% cumulative): NER **83.116** ✓ — includes the commission term `0.5 × (2006 − 91)/19 = 50.3947` ✓
- Ken-Legg JANA Partners: Initial NER **109.611** = 120 − levelized(4 mo free + $35 TI) ✓

**Documented anomaly:** `Ken - Legg` scenario 1 (Western Asset) cell D19 (free-rent levelization) matches the end-of-month factor, while the other seven scenarios match beginning-of-month — an internal inconsistency in the source file (~$0.04/RSF effect), almost certainly a stale hand-edited cell. The beg-of-month convention is taken as canonical.

## Deltas vs the hub's current NER formula (`Lease Comps!AI`, V3.0.0)

The hub's DCF NER shares the model's philosophy (free rent + TI charged nominally/upfront, free rent at the starting rate, levelized to $/RSF/yr, blank when TI unknown) but differs in five ways:

1. **Compounding: annual vs monthly.** Hub discounts yearly cash flows at 6% annually and levelizes with an annual annuity factor; the model discounts monthly at 0.5% and levelizes with a monthly-derived factor (beg-of-month). For a 10-yr lease this shifts NER by roughly 1–2%.
2. **Rent schedule: assumed vs explicit.** Hub assumes 3% annual escalation inside Yr-1/Yr-6/Yr-11 tranches; the model takes an explicit bump schedule (rate × months). The hub's structure is a modeling assumption, not part of the NER math per se — but an explicit-bumps input would let the hub reproduce actual leases exactly.
3. **No commissions or downtime in the hub.** The model levelizes both; the hub has no input columns for them.
4. **Rounding.** The model rounds the levelized base rent to cents before subtracting concessions; the hub doesn't round.
5. **Convention toggle.** The model supports beginning-of-month timing (used in all scenarios); the hub's annual formula has no timing convention.

### Recommended hub change (pending owner approval)

Replace the AI-column formula's annual machinery with the model's monthly machinery, keeping current hub inputs (starting rent, Yr-6/Yr-11 steps or 3% fallback, free months, TI):

- `i = 6%/12`, T = term×12
- Build monthly tranches from the hub's three-tranche rent path (each year's rate held for 12 months)
- `NER = PV_beg/AF_beg − (free/12×start_rent)/AF_beg − TI/AF_beg`
- Optional new inputs, matching the model: downtime months, commission count + schedule (add a `CommissionSchedule` block to Reference).
