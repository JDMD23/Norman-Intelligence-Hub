"""Reference NER implementation, recovered from NER.xls and verified against
every computed cell of its 18 scenarios (see docs/NER_MODEL.md).

Conventions: monthly discounting at annual_rate/12, beginning-of-month
annuities, concessions charged nominally at t=0 and levelized over the term.
"""

from dataclasses import dataclass, field


def af(i_mo: float, months: int, beg: bool = True) -> float:
    """PV annuity factor, in year-units, for $1/RSF/yr paid monthly."""
    if months <= 0:
        return 0.0
    f = (1 - (1 + i_mo) ** -months) / i_mo / 12
    return f * (1 + i_mo) if beg else f


# Cumulative commission schedule "NY Former": yearly incremental rates.
NY_FORMER_YEARLY = {1: .05, 2: .04, 3: .035, 4: .035, 5: .035, 6: .025, 7: .025,
                    8: .025, 9: .025, 10: .025, 11: .02, 12: .02, 13: .02, 14: .02,
                    15: .02, 16: .02, 17: .02, 18: .02, 19: .02, 20: .02,
                    21: .01, 22: .01, 23: .01, 24: .01, 25: .01, 26: .01, 27: .01,
                    28: .01, 29: .01, 30: .01}


def commission_pct(term_years: float, yearly=None) -> float:
    """Cumulative commission %, linearly interpolated on fractional years."""
    yearly = yearly or NY_FORMER_YEARLY
    whole = int(term_years)
    pct = sum(yearly.get(y, 0.0) for y in range(1, whole + 1))
    frac = term_years - whole
    if frac:
        pct += frac * yearly.get(whole + 1, 0.0)
    return pct


@dataclass
class Lease:
    bumps: list          # [(rate $/RSF/yr, months)] — rate may be 0; months>0 counts toward term
    annual_rate: float = 0.06
    free_months: float = 0.0
    ti_psf: float = 0.0
    additional_ti_psf: float = 0.0
    downtime_months: float = 0.0
    n_commissions: float = 0.0
    commission_yearly: dict = field(default_factory=lambda: NY_FORMER_YEARLY)

    def ner(self) -> dict:
        i = self.annual_rate / 12
        T = sum(m for _, m in self.bumps)
        years = T / 12
        r1 = self.bumps[0][0]
        total_rent = sum(r * m / 12 for r, m in self.bumps)

        t, pv_end = 0, 0.0
        for rate, m in self.bumps:
            pv_end += rate * af(i, m, beg=False) * (1 + i) ** -t
            t += m
        afb = af(i, T, beg=True)
        base = round(pv_end * (1 + i) / afb, 2)

        free_nom = self.free_months / 12 * r1
        down_nom = self.downtime_months / 12 * r1
        comm_nom = (self.n_commissions
                    * commission_pct(years, self.commission_yearly)
                    * (total_rent - free_nom) / years) if self.n_commissions else 0.0
        conc = (free_nom + down_nom + self.ti_psf + self.additional_ti_psf + comm_nom) / afb

        return {
            'term_months': T, 'term_years': years, 'total_rent_psf': total_rent,
            'avg_rent_psf': total_rent / years,
            'pv_end': pv_end, 'pv_beg': pv_end * (1 + i),
            'base_annuity': base,
            'concessions_annuity': conc,
            'ner': base - conc,                      # average-NER flavor
            'initial_ner': r1 - conc,                # Ken-Legg flavor
        }


if __name__ == '__main__':
    # NER.xls scenario 1: expect base 91.62, NER 80.603
    s1 = Lease(bumps=[(89, 72), (96, 60)], free_months=12)
    print({k: round(v, 3) for k, v in s1.ner().items()})
    # Scenario 10: expect NER 83.116 (downtime 2, free 12, TI 60, 1 commission)
    s10 = Lease(bumps=[(91, 72), (105, 60), (115, 60), (120, 36)],
                free_months=12, ti_psf=60, downtime_months=2, n_commissions=1)
    print({k: round(v, 3) for k, v in s10.ner().items()})
