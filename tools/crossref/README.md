# Deck cross-reference

Compares broker PowerPoint comp decks against the Lease Comps tab of the Intelligence Hub and
sorts every transaction into: exact, cosmetic-only difference, economics differ, or not in the
hub at all. Read-only — nothing here writes to the workbook.

    python3 tools/crossref/parse_decks.py    # PPTX tables  -> deck_rows.json
    python3 tools/crossref/match2.py         # dedupe + match to the hub -> pairs.json
    python3 tools/crossref/compare.py        # field-by-field diff -> report.json
    python3 tools/crossref/build_xlsx.py     # -> Deck_Crossref.xlsx

Paths are set at the top of each script; point `parse_decks.py` at the deck folder.

## What matching gets wrong if you let it

Three false matches surfaced while building this, each fixed and each worth keeping in mind:

- **Tenant similarity is mandatory.** Building + RSF + date is not enough. Veeva Systems and
  Altana AI took near-identical floor plates at 2 Penn Plaza in the same month, and an earlier
  version merged them into one comp.
- **A tenant can sign twice in one building in one month.** BILT took 39,591 SF on E2-6 and
  58,434 SF on the ground and lower levels at 837 Washington, both September 2025, identical
  rent and TI. RSF closeness is the only signal that separates them, so it breaks ties both when
  picking a candidate and when resolving which transaction owns a hub comp.
- **Addresses are normalised before comparison**, so "28 W 23rd" and "28 West 23rd Street" do not
  register as a difference, but "130 Mercer Street" against "555 Broadway" still does.

Deck rows are also deduplicated against each other first: the same transaction appears in up to
four of the six decks, sometimes with different numbers, and those internal disagreements are
reported rather than silently resolved.
