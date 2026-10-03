"""Synthetic policies with deliberately injected heterogeneity:
county-level frequency differences and vehicle-age effects. The actuarial GLM
should be able to RECOVER these parameters later - the generator encodes signal,
the models prove they can find it."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

COUNTY_FREQ: dict[str, float] = {  # annual claim frequency, per policy
    "Nairobi": 0.085, "Mombasa": 0.075, "Kisumu": 0.115, "Nakuru": 0.090,
    "Kiambu": 0.080, "Uasin Gishu": 0.070, "Machakos": 0.085, "Kajiado": 0.075,
}
COUNTIES = list(COUNTY_FREQ)

VEHICLES = [  # (make, model, base value KES)
    ("Toyota", "Probox", 1_100_000), ("Toyota", "Fielder", 1_400_000),
    ("Toyota", "Harrier", 3_800_000), ("Toyota", "Hilux", 4_100_000),
    ("Nissan", "Note", 950_000), ("Mazda", "Demio", 900_000),
    ("Subaru", "Forester", 2_600_000), ("Isuzu", "NPR", 5_200_000),
    ("Volkswagen", "Golf", 1_900_000), ("Mercedes-Benz", "C200", 3_200_000),
]

SEVERITY_SIGMA = 0.65   # lognormal shape - realistic motor severity dispersion
LOADING = 1.25          # premium = expected loss * loading

FIRST_NAMES = ["Wanjiku", "Otieno", "Kamau", "Achieng", "Mwangi", "Chebet",
               "Barasa", "Nduta", "Omondi", "Njoroge", "Wambui", "Kiptoo"]
LAST_NAMES = ["Kamau", "Odhiambo", "Mutiso", "Korir", "Ndegwa", "Abdi",
              "Mokua", "Wafula", "Kilonzo", "Ochieng"]


@dataclass
class Policy:
    policy_id: str
    customer_name: str
    phone: str
    bank_account: str
    id_number: str
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int
    vehicle_value: float
    sum_insured: float
    annual_premium: float
    county: str
    inception_date: date
    expiry_date: date
    status: str = "ACTIVE"

    @property
    def vehicle_age(self) -> int:
        return 2026 - self.vehicle_year


def severity_mean(vehicle_value: float) -> float:
    """Lognormal mean = exp(mu + sigma^2/2), with mu set so mean severity ~ 30% of value."""
    mu = np.log(0.30 * vehicle_value) - SEVERITY_SIGMA**2 / 2
    return float(np.exp(mu + SEVERITY_SIGMA**2 / 2))


def pure_premium(county: str, vehicle_value: float, vehicle_age: int) -> float:
    freq = COUNTY_FREQ[county] * (1 + 0.02 * vehicle_age)
    return freq * severity_mean(vehicle_value) * LOADING


def generate_policies(n: int, rng: np.random.Generator, ref_date: date) -> list[Policy]:
    policies: list[Policy] = []
    for i in range(n):
        make, model, base_value = VEHICLES[int(rng.integers(len(VEHICLES)))]
        year = int(rng.integers(2008, 2025))
        value = float(base_value * rng.lognormal(0, 0.12))
        county = COUNTIES[int(rng.integers(len(COUNTIES)))]
        inception = ref_date - timedelta(days=int(rng.integers(90, 1700)))
        expiry = inception + timedelta(days=365)
        status = "ACTIVE" if expiry >= ref_date else "LAPSED"
        policies.append(Policy(
            policy_id=f"POL-2026-{i:06d}",
            customer_name=f"{FIRST_NAMES[int(rng.integers(len(FIRST_NAMES)))]} "
                          f"{LAST_NAMES[int(rng.integers(len(LAST_NAMES)))]}",
            phone=f"+2547{int(rng.integers(10_000_000, 99_999_999)):08d}",
            bank_account=f"{int(rng.integers(10_000_000, 99_999_999))}",
            id_number=f"{int(rng.integers(10_000_000, 39_999_999))}",
            vehicle_make=make, vehicle_model=model, vehicle_year=year,
            vehicle_value=round(value, 2),
            sum_insured=round(value * 1.05, 2),
            annual_premium=round(pure_premium(county, value, 2026 - year), 2),
            county=county, inception_date=inception, expiry_date=expiry,
            status=status,
        ))
    return policies
