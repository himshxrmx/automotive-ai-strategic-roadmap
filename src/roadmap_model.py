"""
Bottom-up resource, unit-economics, financial and risk model for the Saarthi Copilot roadmap (Week 1).

Every input is an explicit, labelled assumption (2027 Indian prices, loaded salary costs, component costs from the
Week 3 bill of materials). Change an input and re-run to see the effect on every table and chart.
Outputs: results/*.csv, results/model.json, figures/*.png
Run: python src/roadmap_model.py
"""
import json
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("results", exist_ok=True); os.makedirs("figures", exist_ok=True)
LAKH, CR = 1e5, 1e7

# ------------------------------------------------------------------ 1. phases, team and costs
PHASES = [("P0 Discovery and research", 1, 3), ("P1 Data and prototype", 4, 9), ("P2 Fleet pilot", 10, 15),
          ("P3 Validation and certification", 16, 21), ("P4 Commercial launch", 22, 27), ("P5 OEM integration and scale", 28, 36)]
ROLES = {  # loaded monthly cost per person (salary + 25% for benefits, office, equipment), ₹ lakh / month
    "Product and programme management": 2.0, "Computer vision / ML engineers": 2.2, "Embedded and firmware engineers": 1.8,
    "Hardware and electronics engineers": 1.8, "Cloud, backend and app developers": 1.6, "Data annotation and QA leads": 1.0,
    "Functional safety and cybersecurity": 2.5, "Field operations and customer success": 0.8, "Sales and partnerships": 1.5}
FTE = {  # people per role in each phase P0..P5
    "Product and programme management":      [1, 1, 2, 2, 3, 3],
    "Computer vision / ML engineers":        [2, 4, 5, 6, 6, 7],
    "Embedded and firmware engineers":       [1, 3, 4, 4, 4, 4],
    "Hardware and electronics engineers":    [1, 2, 2, 2, 2, 2],
    "Cloud, backend and app developers":     [0, 1, 3, 3, 4, 5],
    "Data annotation and QA leads":          [0, 1, 2, 2, 3, 3],
    "Functional safety and cybersecurity":   [0, 0, 1, 2, 2, 2],
    "Field operations and customer success": [0, 0, 1, 1, 4, 6],
    "Sales and partnerships":                [0, 0, 0, 1, 3, 4],
}
NONPERS = {  # non-personnel spend per phase, ₹ lakh (what it buys is listed in the report)
    "P0 Discovery and research":       {"Dev kits, tools and licences": 8, "Customer interviews and travel": 4, "Company, legal and IP filing": 5},
    "P1 Data and prototype":           {"20 prototype units": 8, "Test-vehicle lease and fuel": 7, "Data collection and annotation (1,000 h)": 55, "Cloud GPU training": 18},
    "P2 Fleet pilot":                  {"200 pilot units (small batch)": 30, "Installation and field support": 12, "Annotation of pilot data": 25, "Cloud and connectivity": 10, "Pilot insurance and incentives": 8},
    "P3 Validation and certification": {"AIS / EMC / environmental tests at ARAI or ICAT": 95, "Functional safety and SOTIF assessment": 30, "Cybersecurity penetration testing": 15, "Production tooling (enclosure moulds, test jigs)": 30, "Cloud": 10},
    "P4 Commercial launch":            {"Installer network in 10 cities": 45, "Launch marketing": 50, "Insurer pilot": 10, "Cloud and connectivity (fleet)": 20, "Legal and DPDP compliance": 8},
    "P5 OEM integration and scale":    {"OEM integration engineering and samples": 45, "OTA platform hardening": 25, "Cloud and connectivity (scale)": 45, "Marketing and channel": 60, "Compliance and audits": 12},
}
CONTINGENCY = 0.15

phase_rows, monthly_spend, fte_month = [], np.zeros(36), {r: np.zeros(36) for r in ROLES}
for i, (ph, m0, m1) in enumerate(PHASES):
    months = m1 - m0 + 1
    pers = sum(FTE[r][i] * ROLES[r] for r in ROLES) * months
    non = sum(NONPERS[ph].values())
    tot = (pers + non) * (1 + CONTINGENCY)
    phase_rows.append(dict(phase=ph, months=f"{m0}-{m1}", duration=months, headcount=sum(FTE[r][i] for r in ROLES),
                           person_months=sum(FTE[r][i] for r in ROLES) * months, personnel_lakh=round(pers, 1), non_personnel_lakh=non,
                           contingency_lakh=round((pers + non) * CONTINGENCY, 1), total_lakh=round(tot, 1)))
    monthly_spend[m0 - 1:m1] += tot / months
    for r in ROLES:
        fte_month[r][m0 - 1:m1] = FTE[r][i]
ph_df = pd.DataFrame(phase_rows); ph_df.to_csv("results/phase_budget.csv", index=False)
team = pd.DataFrame(FTE, index=[p[0].split()[0] for p in PHASES]).T
team.to_csv("results/team_by_phase.csv")
build_total = ph_df.total_lakh.sum()

# ------------------------------------------------------------------ 2. unit economics
GST = 0.18
# the first-version prices (₹14,999 retail, ₹9,999 fleet kit, ₹249 fleet plan, ₹99 app, ₹115/month running cost) are kept in
# NAIVE for comparison; the report shows why they lose money once GST, channel margin, installation and warranty are counted
NAIVE = dict(retail_price_incl_gst=14999, fleet_price_incl_gst=9999, sub_fleet_incl_gst=249, sub_retail_incl_gst=99,
             sim_data_per_month=70, cloud_per_month=25, support_per_month=20, assembly_test=800)
U = dict(bom=7500, assembly_test=600, packaging_freight=250, warranty_pct_of_net=0.03, install=600,
         retail_price_incl_gst=15999, retail_channel_margin=0.20, fleet_price_incl_gst=11999,
         sub_fleet_incl_gst=299, sub_retail_incl_gst=149, retail_attach=0.30,
         sim_data_per_month=40, cloud_per_month=15, support_per_month=15,
         cac_fleet=1500, cac_retail=1200, churn_fleet_annual=0.15, churn_retail_annual=0.35,
         oem_royalty=1200, oem_support_cost=150)
net = lambda p: p / (1 + GST)  # noqa: E731
unit_cost = U["bom"] + U["assembly_test"] + U["packaging_freight"]
run_cost = U["sim_data_per_month"] + U["cloud_per_month"] + U["support_per_month"]


def channel(name):
    if name == "fleet":
        hw_net = net(U["fleet_price_incl_gst"]); chan = 0.0; sub = net(U["sub_fleet_incl_gst"]); attach = 1.0
        cac, churn = U["cac_fleet"], U["churn_fleet_annual"]
    else:
        hw_net = net(U["retail_price_incl_gst"]); chan = hw_net * U["retail_channel_margin"]; sub = net(U["sub_retail_incl_gst"]); attach = U["retail_attach"]
        cac, churn = U["cac_retail"], U["churn_retail_annual"]
    warranty = hw_net * U["warranty_pct_of_net"]
    hw_margin = hw_net - chan - unit_cost - warranty - U["install"]
    sub_contrib = attach * (sub - run_cost) + (1 - attach) * (-0.3 * run_cost if name == "retail" else 0)  # non-subscribers still use some cloud
    m_churn = 1 - (1 - churn) ** (1 / 12)
    life_m = 1 / m_churn
    ltv = hw_margin + sub_contrib * life_m
    payback = (cac - hw_margin) / sub_contrib if hw_margin < cac and sub_contrib > 0 else 0.0
    return dict(channel=name, hardware_net_of_gst=round(hw_net), channel_margin=round(chan), unit_cost=unit_cost, warranty=round(warranty), installation=U["install"],
                hardware_contribution=round(hw_margin), subscription_net=round(sub, 1), running_cost_per_month=run_cost,
                monthly_contribution=round(sub_contrib, 1), expected_life_months=round(life_m, 1), cac=cac, ltv=round(ltv),
                ltv_to_cac=round(ltv / cac, 1), cac_payback_months=round(payback, 1),
                hardware_gross_margin_pct=round(100 * (hw_net - chan - unit_cost) / (hw_net - chan), 1),
                subscription_gross_margin_pct=round(100 * (sub - run_cost) / sub, 1) if sub else None)


ue = pd.DataFrame([channel("fleet"), channel("retail")]); ue.to_csv("results/unit_economics.csv", index=False)
_save = dict(U); U.update(NAIVE)
unit_cost_naive = U["bom"] + U["assembly_test"] + U["packaging_freight"]
_uc = unit_cost; unit_cost = unit_cost_naive; _rc = run_cost; run_cost = U["sim_data_per_month"] + U["cloud_per_month"] + U["support_per_month"]
ue_naive = pd.DataFrame([channel("fleet"), channel("retail")]); ue_naive.to_csv("results/unit_economics_first_version.csv", index=False)
U = _save; unit_cost = _uc; run_cost = _rc
oem_contrib = U["oem_royalty"] - U["oem_support_cost"]

# ------------------------------------------------------------------ 3. 60-month projection
MONTHS = 60
new_fleet = np.zeros(MONTHS); new_retail = np.zeros(MONTHS); oem_units = np.zeros(MONTHS)
new_fleet[9:15] = 200 / 6                                    # pilot units (given at cost, no subscription revenue)
for m in range(21, MONTHS):                                  # launch at month 22
    k = m - 21
    new_fleet[m] = min(2600, 300 + 70 * k)                   # fleet units added per month, ramping
    new_retail[m] = min(2200, 150 + 55 * k)
for m in range(29, MONTHS):                                  # OEM / Tier-1 factory fitment from month 30
    oem_units[m] = min(9000, 500 + 280 * (m - 29))
OPEX_AFTER = 0                                               # operating cost after month 36 continues at the P5 monthly run-rate (+8%/yr)
p5_month = phase_rows[-1]["total_lakh"] / phase_rows[-1]["duration"] * LAKH
cf = []
act_f = act_r = 0.0
cash = 0.0
mc_f = 1 - (1 - U["churn_fleet_annual"]) ** (1 / 12); mc_r = 1 - (1 - U["churn_retail_annual"]) ** (1 / 12)
fl, rt = channel("fleet"), channel("retail")
for m in range(MONTHS):
    pilot = 9 <= m < 15
    act_f = act_f * (1 - mc_f) + (0 if pilot else new_fleet[m]); act_r = act_r * (1 - mc_r) + new_retail[m]
    rev_hw = (0 if pilot else new_fleet[m]) * fl["hardware_net_of_gst"] + new_retail[m] * (rt["hardware_net_of_gst"] - rt["channel_margin"])
    rev_sub = act_f * fl["subscription_net"] + act_r * U["retail_attach"] * rt["subscription_net"]
    rev_oem = oem_units[m] * U["oem_royalty"]
    cogs = ((0 if pilot else new_fleet[m]) + new_retail[m]) * (unit_cost + U["install"]) + new_fleet[m] * fl["warranty"] * (0 if pilot else 1) + new_retail[m] * rt["warranty"] \
        + (act_f + act_r * (U["retail_attach"] + 0.3 * (1 - U["retail_attach"]))) * run_cost + oem_units[m] * U["oem_support_cost"]
    cac = (0 if pilot else new_fleet[m]) * U["cac_fleet"] + new_retail[m] * U["cac_retail"]
    opex = monthly_spend[m] * LAKH if m < 36 else p5_month * (1.08 ** ((m - 36) / 12))
    if 21 <= m < 36:
        opex -= 0  # launch-phase marketing is inside the phase budgets; CAC is counted separately as variable acquisition cost
    ebitda = rev_hw + rev_sub + rev_oem - cogs - cac - opex
    cash += ebitda
    cf.append(dict(month=m + 1, active_fleet=act_f, active_retail=act_r, oem_units=oem_units[m], revenue=rev_hw + rev_sub + rev_oem,
                   rev_hardware=rev_hw, rev_subscription=rev_sub, rev_oem=rev_oem, cogs=cogs, cac=cac, opex=opex, ebitda=ebitda, cumulative_cash=cash))
cfd = pd.DataFrame(cf); cfd.to_csv("results/monthly_projection.csv", index=False)
cfd["year"] = (cfd.month - 1) // 12 + 1
yr = cfd.groupby("year").agg(revenue=("revenue", "sum"), rev_hardware=("rev_hardware", "sum"), rev_subscription=("rev_subscription", "sum"), rev_oem=("rev_oem", "sum"),
                             cogs=("cogs", "sum"), cac=("cac", "sum"), opex=("opex", "sum"), ebitda=("ebitda", "sum"),
                             active_units_end=("active_fleet", "last"), retail_end=("active_retail", "last"), oem_units=("oem_units", "sum"), cash_end=("cumulative_cash", "last"))
yr["active_units_end"] = yr.active_units_end + yr.retail_end
yr = yr.drop(columns="retail_end")
yr.to_csv("results/annual_pnl.csv")
pos = cfd[cfd.ebitda > 0]
first_pos = None
for m in range(MONTHS):                                      # first month after which EBITDA stays positive
    if (cfd.ebitda.values[m:] > 0).all():
        first_pos = m + 1; break
trough = cfd.cumulative_cash.min(); trough_m = int(cfd.cumulative_cash.idxmin()) + 1
cash_breakeven = next((int(r.month) for r in cfd.itertuples() if r.month > trough_m and r.cumulative_cash >= 0), None)
units_breakeven = None
for r in cfd.itertuples():
    if r.month == first_pos:
        units_breakeven = int(r.active_fleet + r.active_retail)


# ------------------------------------------------------------------ 4. sensitivity
def run_model(over):
    """Re-runs the projection with some inputs changed; returns 5-year cumulative cash and peak funding need."""
    global U
    save = dict(U); vol = over.pop("volume", 1.0); opx = over.pop("opex", 1.0)
    U.update(over)
    f, r = channel("fleet"), channel("retail")
    uc = U["bom"] + U["assembly_test"] + U["packaging_freight"]; rc = U["sim_data_per_month"] + U["cloud_per_month"] + U["support_per_month"]
    mf = 1 - (1 - U["churn_fleet_annual"]) ** (1 / 12); mr = 1 - (1 - U["churn_retail_annual"]) ** (1 / 12)
    af = ar = 0.0; c = 0.0; low = 0.0
    for m in range(MONTHS):
        pilot = 9 <= m < 15
        nf = (0 if pilot else new_fleet[m] * vol); nr = new_retail[m] * vol; ou = oem_units[m] * vol
        af = af * (1 - mf) + nf; ar = ar * (1 - mr) + nr
        rev = nf * f["hardware_net_of_gst"] + nr * (r["hardware_net_of_gst"] - r["channel_margin"]) + af * f["subscription_net"] + ar * U["retail_attach"] * r["subscription_net"] + ou * U["oem_royalty"]
        cost = (nf + nr) * (uc + U["install"]) + nf * f["warranty"] + nr * r["warranty"] + (af + ar * (U["retail_attach"] + 0.3 * (1 - U["retail_attach"]))) * rc + ou * U["oem_support_cost"] \
            + nf * U["cac_fleet"] + nr * U["cac_retail"] + opx * (monthly_spend[m] * LAKH if m < 36 else p5_month * (1.08 ** ((m - 36) / 12)))
        c += rev - cost; low = min(low, c)
    U = save
    return c, low


base_cash, base_low = run_model({})
sens = []
for lab, lo, hi in [("BOM cost ₹6,000 / ₹9,000", {"bom": 6000}, {"bom": 9000}),
                    ("Fleet subscription ₹249 / ₹349 per month", {"sub_fleet_incl_gst": 249}, {"sub_fleet_incl_gst": 349}),
                    ("Unit volumes −30% / +30%", {"volume": 0.7}, {"volume": 1.3}),
                    ("Fleet churn 25% / 8% a year", {"churn_fleet_annual": 0.25}, {"churn_fleet_annual": 0.08}),
                    ("OEM royalty ₹600 / ₹1,800 per vehicle", {"oem_royalty": 600}, {"oem_royalty": 1800}),
                    ("Acquisition cost ×1.5 / ×0.5", {"cac_fleet": 2250, "cac_retail": 1800}, {"cac_fleet": 750, "cac_retail": 600}),
                    ("Fixed operating cost +20% / −20%", {"opex": 1.2}, {"opex": 0.8})]:
    a, al = run_model(dict(lo)); b, bl = run_model(dict(hi))
    sens.append(dict(driver=lab, low_case_cash_cr=round(a / CR, 1), high_case_cash_cr=round(b / CR, 1), low_case_peak_need_cr=round(-al / CR, 1), high_case_peak_need_cr=round(-bl / CR, 1)))
sdf = pd.DataFrame(sens); sdf["swing"] = (sdf.high_case_cash_cr - sdf.low_case_cash_cr).abs(); sdf = sdf.sort_values("swing")
sdf.to_csv("results/sensitivity.csv", index=False)

# ------------------------------------------------------------------ 5. risk register
RISKS = [  # id, category, risk, cause / trigger, L, I, owner, mitigation, contingency, residual L, residual I, phase
    ("R1", "Technical", "Detection accuracy too low in Indian glare, dust, rain and night", "Training data not representative", 4, 5, "ML lead",
     "India-specific dataset (1,000 h, 40% night/rain); HDR camera; scenario test suite (Week 4)", "Add 77 GHz radar variant for fleets; limit features in bad weather", 2, 4, "P1-P3"),
    ("R2", "Technical", "Alert fatigue from false warnings", "Thresholds tuned on foreign data", 4, 4, "Product lead",
     "Thresholds from trade-off analysis (Week 3: 0.85 FCW nuisance/h); < 1 false alert/h as a release gate", "Per-fleet tuning; driver can lower sensitivity of advisories", 2, 3, "P2"),
    ("R3", "Human", "Drivers resist in-cabin cameras (privacy, surveillance fears)", "Monitoring seen as punishment", 3, 4, "Customer success",
     "On-device processing; event-only clips with consent (DPDP Act); coaching, not penalties; drivers see their own data", "Offer forward-only mode; union and driver-council engagement", 2, 3, "P2-P4"),
    ("R4", "Regulatory", "Certification at ARAI/ICAT takes longer than 6 months", "Test-slot queues; first-time design faults", 3, 4, "Safety lead",
     "Pre-compliance EMC tests in P1; early engagement; design to AIS and UN R155/R156 from day one", "Two-month buffer in P3; launch fleet product (aftermarket accessory) first", 2, 3, "P3"),
    ("R5", "Supply", "AI chip shortage or price rise", "Single-source SoC", 3, 4, "Hardware lead",
     "Qualify two SoC vendors; hardware abstraction layer; 6-month buffer stock at launch", "Switch to second vendor (8-week port plan)", 2, 3, "P3-P5"),
    ("R6", "Technical", "Heat failures in hot cabins (70 °C parked)", "Undersized thermal design", 3, 5, "Hardware lead",
     "Thermal budget (Week 3: 76 °C case at 50 °C cabin); summer pilot in Indore and Nagpur; reduced start mode", "Add passive heat sink; restrict peak-load features", 1, 4, "P2-P3"),
    ("R7", "Security", "Cyber attack on connected units", "OTA or cloud compromise", 2, 5, "Security lead",
     "Secure boot, signed OTA, TLS, penetration tests every release", "Remote kill-switch for connectivity; incident response plan", 1, 4, "P3-P5"),
    ("R8", "Legal", "Liability claim after a missed warning", "Customer expects crash prevention", 2, 5, "CEO / legal",
     "Warning-only positioning; clear user agreement; safety case documentation; product liability insurance", "Insurer-backed legal cover", 1, 4, "P4-P5"),
    ("R9", "Market", "OEMs and global Tier-1s launch cheaper factory ADAS", "Bharat NCAP pushes OEM-fitted ADAS", 3, 4, "CEO",
     "Focus on retrofit and fleets (installed base of millions); license the software stack to OEMs", "Pivot revenue towards licensing", 3, 3, "P4-P5"),
    ("R10", "Commercial", "Fleet sales cycle longer than planned (6+ months)", "Procurement committees, trials", 4, 3, "Sales lead",
     "Pilot customers become references; ROI calculator (fuel, insurance, downtime); 30-day free trial", "Channel partners (telematics vendors, insurers)", 3, 2, "P4"),
    ("R11", "Financial", "Funding round delayed or smaller", "Weak pilot results or market downturn", 3, 5, "CEO",
     "Stage-gated spending; raise seed for P0-P2 only; milestone M5 as the proof point", "Cut P5 scope; extend runway by 6 months with a smaller team", 2, 4, "P2-P3"),
    ("R12", "People", "Loss of key ML engineers", "Competition from large tech firms", 3, 4, "CTO",
     "ESOPs; documentation and pair ownership of every model; university partnerships", "Contract specialists for gaps", 2, 3, "All"),
    ("R13", "Data", "Annotation quality or cost overruns", "Complex Indian scenes, many classes", 3, 3, "Data lead",
     "Clear labelling guide; 10% audit sample; auto-labelling and active learning", "Second annotation vendor", 2, 2, "P1-P2"),
    ("R14", "Regulatory", "DPDP rules require changes to data handling", "New rules or Data Protection Board guidance", 3, 3, "Legal",
     "Privacy by design; data minimisation; consent management built in", "Rapid OTA update of data flows", 2, 2, "P3-P5"),
    ("R15", "Operations", "Poor installations in the aftermarket (wrong angle, loose power)", "Untrained installers", 4, 3, "Field ops lead",
     "Installer certification; guided calibration app; installation photo check", "Remote diagnostics and re-visit within 48 h", 2, 2, "P4-P5"),
]
rk = pd.DataFrame(RISKS, columns=["id", "category", "risk", "cause", "L", "I", "owner", "mitigation", "contingency", "rL", "rI", "phase"])
rk["score"] = rk.L * rk.I; rk["residual"] = rk.rL * rk.rI
rk = rk.sort_values("score", ascending=False); rk.to_csv("results/risk_register.csv", index=False)

# ------------------------------------------------------------------ summary JSON
OUT = dict(build_budget_lakh=round(build_total, 1), build_budget_cr=round(build_total / 100, 2), contingency=CONTINGENCY,
           person_months=int(ph_df.person_months.sum()), peak_headcount=int(ph_df.headcount.max()),
           unit_cost=unit_cost, running_cost_per_month=run_cost, unit_economics=ue.to_dict("records"), unit_economics_first_version=ue_naive.to_dict("records"), oem_contribution_per_vehicle=oem_contrib,
           first_month_ebitda_stays_positive=first_pos, active_units_at_breakeven=units_breakeven, peak_funding_need_cr=round(-trough / CR, 2), peak_funding_month=trough_m,
           cash_breakeven_month=cash_breakeven, five_year_cumulative_cash_cr=round(cfd.cumulative_cash.iloc[-1] / CR, 2),
           annual=yr.round(0).to_dict("index"), sensitivity_base_cash_cr=round(base_cash / CR, 1), inputs=U)
json.dump(OUT, open("results/model.json", "w"), indent=2, default=float)

# ------------------------------------------------------------------ figures
cols = plt.cm.tab10.colors
fig, ax = plt.subplots(figsize=(10, 5.2))
bottom = np.zeros(36)
for i, r in enumerate(ROLES):
    ax.bar(np.arange(1, 37), fte_month[r], bottom=bottom, color=cols[i % 10], width=1.0, label=r)
    bottom += fte_month[r]
ax2 = ax.twinx(); ax2.plot(np.arange(1, 37), np.cumsum(monthly_spend) / 100, "k-", lw=2, label="cumulative spend (₹ crore)")
ax.set_xlabel("month"); ax.set_ylabel("people (FTE)"); ax2.set_ylabel("cumulative spend (₹ crore)")
for ph, m0, m1 in PHASES:
    ax.axvline(m0 - 0.5, color="grey", lw=0.6); ax.text((m0 + m1) / 2, bottom.max() + 1.2, ph.split()[0], ha="center", fontsize=8)
ax.set_ylim(0, bottom.max() + 3); ax.set_title("Team build-up by role and cumulative spend over the 36-month roadmap")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=4); fig.tight_layout(); fig.savefig("figures/fig2_team_and_spend.png", dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 4.2))
ax.plot(cfd.month, cfd.cumulative_cash / CR, "b-", lw=2, label="cumulative cash (₹ crore)")
ax.bar(cfd.month, cfd.ebitda / CR, color=["#d62728" if v < 0 else "#2ca02c" for v in cfd.ebitda], alpha=0.6, label="monthly EBITDA (₹ crore)")
ax.axhline(0, color="k", lw=0.8)
ax.annotate(f"peak funding need ₹{-trough / CR:.1f} cr (month {trough_m})", (trough_m, trough / CR), xytext=(trough_m - 30, trough / CR + 7), arrowprops=dict(arrowstyle="->"), fontsize=8)
if first_pos:
    ax.axvline(first_pos, color="#2ca02c", ls=":", lw=1); ax.text(first_pos + 0.5, cfd.cumulative_cash.max() / CR * 0.6 if cfd.cumulative_cash.max() > 0 else 1, f"EBITDA positive from month {first_pos}", fontsize=8)
ax.set_xlabel("month from start (launch at month 22)"); ax.set_ylabel("₹ crore"); ax.set_title("Five-year cash flow: build phase, launch, and break-even"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig("figures/fig3_cash_flow.png", dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 4))
y = np.arange(len(sdf))
for i, r in enumerate(sdf.itertuples()):
    lo, hi = sorted([r.low_case_cash_cr, r.high_case_cash_cr])
    ax.barh(i, hi - lo, left=lo, color="#1f77b4")
ax.axvline(base_cash / CR, color="k", lw=1); ax.text(base_cash / CR, len(sdf) - 0.4, f"base ₹{base_cash / CR:.1f} cr", fontsize=8, ha="center")
ax.set_yticks(y); ax.set_yticklabels(sdf.driver, fontsize=8); ax.set_xlabel("cumulative cash after 5 years (₹ crore)")
ax.set_title("Sensitivity: which assumptions move the outcome most"); ax.grid(axis="x", alpha=0.3)
fig.tight_layout(); fig.savefig("figures/fig4_sensitivity.png", dpi=160); plt.close(fig)

fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
for ax, (lc, ic, title) in zip(axs, [("L", "I", "Before mitigation"), ("rL", "rI", "After mitigation")]):
    grid = np.add.outer(np.arange(1, 6), np.arange(1, 6))
    ax.imshow(np.outer(np.arange(1, 6), np.arange(1, 6)), origin="lower", cmap="RdYlGn_r", extent=(0.5, 5.5, 0.5, 5.5), alpha=0.55, vmin=1, vmax=25)
    for (l, i), g in rk.groupby([lc, ic]):
        ax.text(i, l, "\n".join(g.id), ha="center", va="center", fontsize=7.5)
    ax.set_xlabel("impact (1-5)"); ax.set_ylabel("likelihood (1-5)"); ax.set_title(title); ax.set_xticks(range(1, 6)); ax.set_yticks(range(1, 6))
fig.suptitle("Risk heat map of the 15 registered risks"); fig.tight_layout(); fig.savefig("figures/fig5_risk_heatmap.png", dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(8.5, 3.8))
xs = np.arange(1, 6)
ax.bar(xs - 0.25, yr.rev_hardware / CR, 0.25, label="hardware"); ax.bar(xs, yr.rev_subscription / CR, 0.25, label="subscriptions"); ax.bar(xs + 0.25, yr.rev_oem / CR, 0.25, label="OEM royalties")
ax.plot(xs, yr.ebitda / CR, "ko-", label="EBITDA"); ax.axhline(0, color="k", lw=0.6)
ax.set_xticks(xs); ax.set_xticklabels([f"Year {i}\n({2026 + i})" for i in xs]); ax.set_ylabel("₹ crore"); ax.set_title("Revenue mix and EBITDA by year"); ax.legend(fontsize=8); ax.grid(axis="y", alpha=0.3)
fig.tight_layout(); fig.savefig("figures/fig6_revenue_mix.png", dpi=160); plt.close(fig)

print(ph_df.to_string()); print("build total ₹ lakh", round(build_total, 1)); print(ue.T.to_string()); print(yr.round(0).to_string())
print({k: OUT[k] for k in ["first_month_ebitda_stays_positive", "active_units_at_breakeven", "peak_funding_need_cr", "peak_funding_month", "cash_breakeven_month", "five_year_cumulative_cash_cr", "person_months"]})
print(sdf.to_string())
