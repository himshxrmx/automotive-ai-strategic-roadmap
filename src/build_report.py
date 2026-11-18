"""
Builds the Week 1 strategic roadmap (.docx) from the roadmap model and the reusable text blocks.
Run from the week folder:  python src/roadmap_model.py  then  python src/build_report.py
"""
import json
import sys

import pandas as pd

sys.path.insert(0, "src")
from doclib import Report, section  # noqa: E402

OUT = "Week1_Strategic_Roadmap_Automotive_AI.docx"
GH = "https://github.com/himshxrmx/automotive-ai-strategic-roadmap"
B = json.load(open("content/base_text.json", encoding="utf-8"))


def fix(blocks, repl):
    def f(x):
        if isinstance(x, str):
            for a, b in repl.items():
                x = x.replace(a, b)
            return x
        return [f(i) for i in x] if isinstance(x, list) else x
    return [f(b) for b in blocks]


B = fix(B, {"25,000 active units; positive unit economics": "about 18,000 active fleet and retail units plus OEM fitment; EBITDA-positive path (month 48)",
            "Signed OEM/Tier-1 agreement; 25,000 active units; platform v3": "Signed OEM/Tier-1 agreement; about 18,000 active units plus factory fitment; platform v3",
            "25,000": "about 18,000 (plus OEM fitment)"})
M = json.load(open("results/model.json"))
ph = pd.read_csv("results/phase_budget.csv"); team = pd.read_csv("results/team_by_phase.csv", index_col=0)
ue = pd.read_csv("results/unit_economics.csv").set_index("channel"); ue0 = pd.read_csv("results/unit_economics_first_version.csv").set_index("channel")
yr = pd.read_csv("results/annual_pnl.csv"); sens = pd.read_csv("results/sensitivity.csv").sort_values("swing", ascending=False)
rk = pd.read_csv("results/risk_register.csv"); U = M["inputs"]
IMG = ["images/roadmap_gantt.png"]
CR = 1e7
cr = lambda v: (f"₹{v / CR:,.1f} cr" if v >= 0 else f"−₹{-v / CR:,.1f} cr")  # noqa: E731
rs = lambda v: (f"₹{v:,.0f}" if v >= 0 else f"−₹{-v:,.0f}")  # noqa: E731
f, r = ue.loc["fleet"], ue.loc["retail"]; f0, r0 = ue0.loc["fleet"], ue0.loc["retail"]
y5 = yr.iloc[-1]

R = Report()
R.title_page("Strategic Roadmap for Automotive AI Innovation",
             "Saarthi Copilot: an affordable edge-AI driver safety co-pilot for Indian roads, with a bottom-up resource, unit-economics and risk model",
             ["Week 1 · Automotive AI Innovation Internship (YuvaIntern)", "Author: Him Sharma, B.Tech CSE, ABES Engineering College",
              "November 2026", f"Financial model, risk register and figures: {GH}"])

# ------------------------------------------------------------------ 1
R.h1("1. Executive Summary")
R.p("Road crashes kill about 1.19 million people worldwide every year, and India carries a heavy share: in 2022 the country recorded 4,61,312 road "
    "accidents and 1,68,491 deaths, most of them traced to human factors such as fatigue, distraction and over-speeding. Advanced driver assistance "
    "systems can prevent many of these crashes, but in India they are still found mainly on top variants of new cars and are tuned for orderly roads.")
R.p("This report sets out a 36-month roadmap for Saarthi Copilot, an affordable windscreen device that combines in-cabin driver monitoring, forward "
    "collision and lane warnings tuned for Indian traffic, vehicle-health alerts from the OBD-II port and multilingual voice alerts, with all video "
    "processed on the device. It moves through six stage-gated phases: discovery, data and prototype, a 200-vehicle fleet pilot, certification, "
    "commercial launch at month 22, and OEM integration.")
R.p("Every number in the plan comes from a bottom-up model published with this report (src/roadmap_model.py):")
R.bullets([
    ("Resources by phase:", f"the team grows from 5 to {M['peak_headcount']} people across nine roles, {M['person_months']} person-months in total. The 36-month build "
     f"costs {cr(M['build_budget_lakh'] * 1e5)} including a 15% contingency, from ₹0.54 crore in discovery to ₹8.26 crore in the OEM-integration phase."),
    ("Unit economics:", f"a check of the first-draft pricing showed that fleet hardware would have been sold at a loss of ₹{-f0.hardware_contribution:,.0f} per unit once GST, "
     f"installation and warranty are counted. Revised pricing (fleet kit ₹{U['fleet_price_incl_gst']:,} plus ₹{U['sub_fleet_incl_gst']} a month) earns "
     f"₹{f.hardware_contribution:,.0f} on the hardware and ₹{f.monthly_contribution:.0f} a month per vehicle, a lifetime value of ₹{f.ltv:,.0f} against ₹{f.cac:,.0f} to win the customer ({f.ltv_to_cac}×)."),
    ("Break-even:", f"operating profit (EBITDA) turns positive from month {M['first_month_ebitda_stays_positive']} at about {M['active_units_at_breakeven']:,} active "
     f"units. The peak funding need is {cr(M['peak_funding_need_cr'] * CR)} at month {M['peak_funding_month']}; year-5 revenue is {cr(y5.revenue)} with EBITDA of {cr(y5.ebitda)}."),
    ("What matters most:", "a sensitivity analysis shows that the bill of materials is the single biggest lever (₹6,000 against ₹9,000 per unit swings 5-year cash "
     "by about ₹33 crore), followed by fixed operating cost and the OEM royalty."),
    ("Risk register:", "15 risks are scored for likelihood and impact before and after mitigation, each with an owner, a mitigation, a contingency and "
     "the phase in which it matters. The top risks are detection accuracy in Indian conditions, alert fatigue and a delayed funding round."),
])

# ------------------------------------------------------------------ 2-6 (kept), business model rewritten
R.emit(section(B, "2. Introduction to the AI Solution Concept"))
R.emit(section(B, "3. Market Analysis"), drop={"3.6 Business Model"})
R.h2("3.6 Business Model")
R.p("The business model has three revenue streams, priced so that each covers its own cost (Section 9 shows the arithmetic):")
R.bullets([
    ("Fleet subscription (main channel):", f"hardware kit at ₹{U['fleet_price_incl_gst']:,} including GST, plus ₹{U['sub_fleet_incl_gst']} per vehicle per month for the "
     "dashboard, driver coaching, event video and over-the-air updates. Fleets buy on return on investment: fewer crashes, lower insurance and less downtime."),
    ("Aftermarket retail:", f"a kit for private car owners at ₹{U['retail_price_incl_gst']:,} through accessory dealers, with an optional ₹{U['sub_retail_incl_gst']}-a-month app plan."),
    ("Software licensing:", f"a royalty of about ₹{U['oem_royalty']:,} per vehicle from vehicle makers and Tier-1 suppliers who fit the Saarthi software at the factory, from month 30."),
    ("Insurer partnerships:", "anonymised, consent-based driving-risk scores for usage-based insurance, treated as upside and not counted in the projections."),
])
R.emit(section(B, "4. Technology Trends"))
R.emit(section(B, "5. Pain Points in Current Automotive Solutions"))
R.emit(section(B, "6. High-Level System Architecture"))
R.emit(section(B, "7. Strategic Roadmap and Timeline"), images=IMG)

# ------------------------------------------------------------------ 8 resources
R.h1("8. Resource Estimates by Phase")
R.p("The resource plan is built bottom-up: people per role per phase, multiplied by a loaded monthly cost per role (salary plus about 25% for "
    "benefits, office and equipment, at 2027 Indian start-up rates), plus the non-personnel spend each phase needs, plus a 15% contingency.")
R.h2("8.1 Team by Role and Phase")
roles = list(team.index)
rates = {"Product and programme management": 2.0, "Computer vision / ML engineers": 2.2, "Embedded and firmware engineers": 1.8, "Hardware and electronics engineers": 1.8,
         "Cloud, backend and app developers": 1.6, "Data annotation and QA leads": 1.0, "Functional safety and cybersecurity": 2.5,
         "Field operations and customer success": 0.8, "Sales and partnerships": 1.5}
rows = [[ro, f"₹{rates[ro]:.1f} L"] + [str(int(v)) for v in team.loc[ro].values] for ro in roles]
rows.append(["Total headcount", ""] + [str(int(v)) for v in team.sum().values])
R.table(["Role", "Cost / month", "P0", "P1", "P2", "P3", "P4", "P5"], rows, caption="People per role in each phase (L = ₹ lakh, loaded monthly cost per person)",
        widths=[5.8, 2.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2], font=9)
R.p("Bulk data labelling is outsourced to an annotation partner and managed by the in-house annotation and QA leads. Functional-safety and "
    "cybersecurity specialists join in the pilot phase, when the safety case starts, and field operations grow fastest at launch, when installations begin.")
R.h2("8.2 Budget by Phase")
rows = [[p.phase, p.months, str(p.headcount), str(p.person_months), f"{p.personnel_lakh:.0f}", f"{p.non_personnel_lakh:.0f}", f"{p.contingency_lakh:.0f}", f"{p.total_lakh:.0f}"] for p in ph.itertuples()]
rows.append(["Total", "1-36", "", str(int(ph.person_months.sum())), f"{ph.personnel_lakh.sum():.0f}", f"{ph.non_personnel_lakh.sum():.0f}", f"{ph.contingency_lakh.sum():.0f}", f"{ph.total_lakh.sum():.0f}"])
R.table(["Phase", "Months", "Head-count", "Person-months", "People (₹ L)", "Other (₹ L)", "Contingency (₹ L)", "Total (₹ L)"], rows,
        caption="Resource and budget estimate for each phase (₹ lakh)", widths=[4.6, 1.4, 1.5, 1.7, 1.8, 1.7, 2.0, 1.7], font=8.5)
R.p(f"The 36-month build costs about ₹{ph.total_lakh.sum() / 100:.1f} crore. People are {100 * ph.personnel_lakh.sum() / (ph.personnel_lakh.sum() + ph.non_personnel_lakh.sum()):.0f}% of "
    "spend before contingency, which is typical of a software-heavy hardware start-up. The most expensive single non-personnel item is certification in P3 "
    "(₹95 lakh for AIS, EMC and environmental testing at ARAI or ICAT), which is why pre-compliance testing starts in P1.")
R.h2("8.3 What Each Phase's Non-Personnel Budget Buys")
nonp = {"P0 Discovery and research": "dev kits, tools and licences ₹8 L; 30+ customer interviews and travel ₹4 L; company set-up, legal and IP filing ₹5 L",
        "P1 Data and prototype": "20 prototype units ₹8 L; test-vehicle lease ₹7 L; collection and annotation of 1,000 hours of road and cabin video ₹55 L; cloud GPU training ₹18 L",
        "P2 Fleet pilot": "200 pilot units ₹30 L; installation and field support ₹12 L; annotation of pilot data ₹25 L; cloud and connectivity ₹10 L; pilot insurance and driver incentives ₹8 L",
        "P3 Validation and certification": "AIS, EMC and environmental tests ₹95 L; functional safety and SOTIF assessment ₹30 L; penetration testing ₹15 L; production tooling (moulds, test jigs) ₹30 L; cloud ₹10 L",
        "P4 Commercial launch": "installer network in 10 cities ₹45 L; launch marketing ₹50 L; insurer pilot ₹10 L; fleet cloud and connectivity ₹20 L; legal and DPDP compliance ₹8 L",
        "P5 OEM integration and scale": "OEM integration engineering and samples ₹45 L; OTA platform hardening ₹25 L; cloud at scale ₹45 L; marketing and channel ₹60 L; audits ₹12 L"}
R.table(["Phase", "Main non-personnel items"], [[k, v] for k, v in nonp.items()], caption="Non-personnel spend by phase", widths=[4.2, 12.3], font=9)
R.figure("figures/fig2_team_and_spend.png", "Team build-up by role and cumulative spend over 36 months")
R.h2("8.4 Funding Plan")
seed = ph.total_lakh.iloc[:3].sum() / 100; a_round = ph.total_lakh.iloc[3:5].sum() / 100
R.p(f"Spending is stage-gated so that each round is raised on proof, not promises. A seed round of about ₹{seed:.1f} crore covers P0–P2 and ends with the pilot "
    f"results at milestone M5 (month 15). A Series A of about ₹{a_round:.1f} crore funds certification and launch (P3–P4). Because the business only becomes "
    f"cash-generative at month {M['first_month_ebitda_stays_positive']}, the total funding needed, including post-launch operations, is about "
    f"₹{M['peak_funding_need_cr']:.1f} crore, reached at month {M['peak_funding_month']}; the balance is raised as a Series A extension once launch traction is visible. "
    "Government schemes such as the Startup India Seed Fund and Fund of Funds, and grants for road-safety innovation, can reduce the equity needed.")
R.emit(section(B, "8.3 Hardware and Infrastructure"), rename={"8.3 Hardware and Infrastructure": "8.5 Hardware and Infrastructure"})

# ------------------------------------------------------------------ 9 unit economics
R.h1("9. Unit Economics")
R.h2("9.1 Checking the First-Draft Pricing")
R.p("The first draft of this roadmap priced the kit at ₹14,999 for retail and planned volume discounts for fleets, with a ₹249 monthly fleet subscription, "
    "and assumed a hardware margin of about 30%. Working through a single unit exposes three costs the draft ignored: 18% GST is collected for the "
    "government and is not revenue; a retail dealer keeps about 20% of the net price; and every unit needs installation (about ₹600) and a warranty provision (3%).")
rows = [["Price to customer, including GST", "₹9,999", "₹14,999"],
        ["Net revenue after 18% GST", f"₹{f0.hardware_net_of_gst:,.0f}", f"₹{r0.hardware_net_of_gst:,.0f}"],
        ["Dealer margin (20%)", "-", f"−₹{r0.channel_margin:,.0f}"],
        ["Unit cost (BOM ₹7,500 + assembly ₹800 + packing and freight ₹250)", f"−₹{f0.unit_cost:,.0f}", f"−₹{r0.unit_cost:,.0f}"],
        ["Warranty provision (3%)", f"−₹{f0.warranty:,.0f}", f"−₹{r0.warranty:,.0f}"],
        ["Installation", f"−₹{f0.installation:,.0f}", f"−₹{r0.installation:,.0f}"],
        ["Hardware contribution per unit", rs(f0.hardware_contribution), rs(r0.hardware_contribution)],
        ["Monthly subscription contribution (net price − ₹115 running cost)", rs(f0.monthly_contribution), rs(r0.monthly_contribution)]]
R.table(["First-draft unit economics", "Fleet", "Retail"], rows, caption="First-draft pricing checked unit by unit", widths=[9.5, 3.4, 3.4], font=9)
R.p("Fleet hardware lost money on every unit, and the retail app plan cost more to run (4G data, cloud and support at ₹115 a month) than it earned "
    "after GST. A roadmap built on those numbers would have grown its losses with every sale.")
R.h2("9.2 Revised Pricing and Costs")
R.p("Three changes fix the economics. Event-only uploads (short clips around warnings instead of continuous telemetry) cut 4G data to about 300 MB a month, "
    "reducing the running cost to ₹70 per device per month (₹40 data, ₹15 cloud, ₹15 support). Assembly falls to ₹600 at volume. And prices move to "
    f"₹{U['fleet_price_incl_gst']:,} plus ₹{U['sub_fleet_incl_gst']} a month for fleets and ₹{U['retail_price_incl_gst']:,} for retail, still well below factory-fitted ADAS packs.")
rows = [["Price to customer, including GST", f"₹{U['fleet_price_incl_gst']:,}", f"₹{U['retail_price_incl_gst']:,}"],
        ["Net revenue after 18% GST", f"₹{f.hardware_net_of_gst:,.0f}", f"₹{r.hardware_net_of_gst:,.0f}"],
        ["Dealer margin (20%)", "-", f"−₹{r.channel_margin:,.0f}"],
        ["Unit cost (BOM ₹7,500 + assembly ₹600 + packing and freight ₹250)", f"−₹{f.unit_cost:,.0f}", f"−₹{r.unit_cost:,.0f}"],
        ["Warranty provision (3%)", f"−₹{f.warranty:,.0f}", f"−₹{r.warranty:,.0f}"],
        ["Installation", f"−₹{f.installation:,.0f}", f"−₹{r.installation:,.0f}"],
        ["Hardware contribution per unit", f"₹{f.hardware_contribution:,.0f}", f"₹{r.hardware_contribution:,.0f}"],
        ["Hardware gross margin", f"{f.hardware_gross_margin_pct:.1f}%", f"{r.hardware_gross_margin_pct:.1f}%"],
        ["Subscription net of GST, per month", f"₹{f.subscription_net:.0f}", f"₹{r.subscription_net:.0f} (30% of buyers)"],
        ["Running cost per active device, per month", f"₹{f.running_cost_per_month:.0f}", f"₹{r.running_cost_per_month:.0f}"],
        ["Monthly contribution per device", f"₹{f.monthly_contribution:.0f}", f"₹{r.monthly_contribution:.0f}"],
        ["Subscription gross margin", f"{f.subscription_gross_margin_pct:.1f}%", f"{r.subscription_gross_margin_pct:.1f}%"],
        ["Churn per year / expected life", f"{U['churn_fleet_annual']:.0%} / {f.expected_life_months:.0f} months", f"{U['churn_retail_annual']:.0%} / {r.expected_life_months:.0f} months"],
        ["Customer acquisition cost (CAC)", f"₹{f.cac:,.0f}", f"₹{r.cac:,.0f}"],
        ["Lifetime value (LTV)", f"₹{f.ltv:,.0f}", f"₹{r.ltv:,.0f}"],
        ["LTV / CAC", f"{f.ltv_to_cac}×", f"{r.ltv_to_cac}×"],
        ["Months to recover CAC", f"{f.cac_payback_months:.1f}", "recovered on the hardware sale"]]
R.table(["Revised unit economics", "Fleet", "Retail"], rows, caption="Revised unit economics per vehicle", widths=[9.5, 3.4, 3.4], font=9)
R.p(f"Worked example for one fleet vehicle: the fleet pays ₹{U['fleet_price_incl_gst']:,}, of which ₹{U['fleet_price_incl_gst'] - f.hardware_net_of_gst:,.0f} is GST. After the unit cost, "
    f"warranty and installation, Saarthi keeps ₹{f.hardware_contribution:,.0f}. Each month the vehicle pays ₹{U['sub_fleet_incl_gst']} (₹{f.subscription_net:.0f} after GST) and costs ₹70 "
    f"to serve, leaving ₹{f.monthly_contribution:.0f}. With 15% of fleet vehicles leaving each year, the average vehicle stays about {f.expected_life_months:.0f} months, so its "
    f"lifetime value is ₹{f.hardware_contribution:,.0f} + {f.expected_life_months:.0f} × ₹{f.monthly_contribution:.0f} ≈ ₹{f.ltv:,.0f}, about {f.ltv_to_cac} times the ₹{f.cac:,.0f} "
    f"it costs to win. The acquisition cost is recovered in about {f.cac_payback_months:.0f} months.")
R.p(f"Retail is weaker: the hardware contribution of ₹{r.hardware_contribution:,.0f} covers acquisition, but app subscriptions barely cover their running cost and "
    f"private owners churn faster, so LTV/CAC is only {r.ltv_to_cac}×. This is why the strategy leads with fleets and treats retail mainly as a brand and "
    f"volume channel. Factory licensing is the most profitable stream: each OEM vehicle contributes about ₹{M['oem_contribution_per_vehicle']:,} "
    f"(₹{U['oem_royalty']:,} royalty less ₹{U['oem_support_cost']} of support) with no hardware, installation or acquisition cost.")

# ------------------------------------------------------------------ 10 projection
R.h1("10. Five-Year Financial Projection")
R.p("The projection runs month by month for 60 months. Fleet installations start at 300 units a month at launch (month 22) and ramp to 2,600; retail "
    "starts at 150 and ramps to 2,200; factory fitment through an OEM or Tier-1 partner starts at month 30 and ramps to 9,000 vehicles a month. Fixed "
    "operating cost follows the phase budgets to month 36 and then grows 8% a year. Customer acquisition costs are counted per unit sold.")
rows = []
for y in yr.itertuples():
    rows.append([f"Year {y.year} ({2026 + y.year})", f"{y.revenue / CR:.1f}", f"{y.rev_hardware / CR:.1f}", f"{y.rev_subscription / CR:.1f}", f"{y.rev_oem / CR:.1f}",
                 f"{(y.cogs + y.cac) / CR:.1f}", f"{y.opex / CR:.1f}", f"{y.ebitda / CR:.1f}", f"{y.active_units_end:,.0f}", f"{y.cash_end / CR:.1f}"])
R.table(["Year", "Revenue", "Hardware", "Subscr.", "OEM", "Unit costs + CAC", "Fixed cost", "EBITDA", "Active units (end)", "Cumulative cash"], rows,
        caption="Annual projection (₹ crore except units)", widths=[2.4, 1.5, 1.6, 1.4, 1.2, 1.9, 1.6, 1.5, 1.9, 1.8], font=8)
R.figure("figures/fig3_cash_flow.png", "Monthly EBITDA and cumulative cash over five years")
R.figure("figures/fig6_revenue_mix.png", "Revenue by stream and EBITDA by year", width_cm=13)
R.p(f"Monthly EBITDA turns permanently positive at month {M['first_month_ebitda_stays_positive']}, with about {M['active_units_at_breakeven']:,} subscribing devices in the field. "
    f"Cumulative cash bottoms out at −₹{M['peak_funding_need_cr']:.1f} crore in month {M['peak_funding_month']}, which sets the total funding need. By year 5 the company "
    f"earns {cr(y5.revenue)} of revenue and {cr(y5.ebitda)} of EBITDA, with recurring subscriptions and royalties making up "
    f"{100 * (y5.rev_subscription + y5.rev_oem) / y5.revenue:.0f}% of revenue. Hardware dominates revenue but earns thin margins; subscriptions and OEM royalties earn most of the profit, "
    "which is the reason to build the licensing business in P5.")
R.h2("10.1 Sensitivity Analysis")
rows = [[s.driver, f"{s.low_case_cash_cr:.1f}", f"{s.high_case_cash_cr:.1f}", f"{s.swing:.1f}", f"{max(s.low_case_peak_need_cr, s.high_case_peak_need_cr):.1f}"] for s in sens.itertuples()]
R.table(["Assumption changed (low / high)", "5-year cash, low (₹ cr)", "5-year cash, high (₹ cr)", "Swing (₹ cr)", "Worst peak funding (₹ cr)"], rows,
        caption=f"Effect of each assumption on 5-year cumulative cash (base case {cr(M['sensitivity_base_cash_cr'] * CR)})", widths=[5.8, 2.6, 2.6, 2.0, 3.0], font=8.5)
R.figure("figures/fig4_sensitivity.png", "Tornado chart: change in 5-year cumulative cash for each assumption", width_cm=13.5)
R.p("The bill of materials is by far the biggest lever: every ₹1,000 saved per unit is worth about ₹11 crore over five years, because it applies to every "
    "unit sold. This justifies the Week 3 work to fit the design on an 8 TOPS automotive SoC rather than a more expensive module, and dual-sourcing the "
    "chip. Fixed operating cost and the OEM royalty come next; churn matters least over five years because most fleet vehicles are still in their first contract. "
    "Even in the worst single case the funding need stays at about ₹37 crore, so the plan is robust to any one assumption being wrong, though not to several at once.")

# ------------------------------------------------------------------ 11 risks
R.h1("11. Risk Register")
R.p("Each risk is scored for likelihood (L) and impact (I) on a 1–5 scale; the score L × I ranks them. Each has an owner, a mitigation that is part of the "
    "plan and budget, a contingency that is triggered if the risk occurs, the phase in which it matters, and a residual score after mitigation. Risks scoring "
    "12 or more are reviewed at every monthly leadership meeting and at each phase gate.")
rows = [[x.id, x.category, x.risk, str(x.L), str(x.I), str(x.score), x.owner, x.mitigation, x.contingency, f"{x.rL}×{x.rI}={x.residual}", x.phase] for x in rk.itertuples()]
R.table(["ID", "Category", "Risk", "L", "I", "Score", "Owner", "Mitigation (planned)", "Contingency (if it happens)", "Residual", "Phase"], rows,
        caption="Risk register, sorted by score before mitigation", widths=[0.8, 1.5, 2.8, 0.6, 0.6, 0.9, 1.5, 3.5, 2.8, 1.4, 1.0], font=7)
R.figure("figures/fig5_risk_heatmap.png", "Likelihood-impact heat map before and after mitigation")
R.p(f"Before mitigation, {int((rk.score >= 12).sum())} of the 15 risks score 12 or more; after mitigation, {int((rk.residual >= 12).sum())} do. The largest residual risk is market "
    "competition from OEM-fitted ADAS (R9), which mitigation can reduce only partly. The strategic answer is in the business model itself: if OEMs fit "
    "ADAS at the factory, Saarthi aims to be the software inside it through licensing, while the retrofit market of tens of millions of existing vehicles "
    "remains open.")
R.emit(section(B, "10. Success Metrics"), rename={"10. Success Metrics": "12. Success Metrics"})

# ------------------------------------------------------------------ 13
R.h1("13. Conclusion")
R.p("India's road-safety challenge is driven largely by human factors that AI can now detect in real time and at low cost. Saarthi Copilot brings driver "
    "monitoring, India-tuned forward warnings, vehicle-health alerts and multilingual voice alerts into one edge-AI device aimed at the large fleet and "
    "retrofit market that factory ADAS does not reach.")
R.p(f"The roadmap is now backed by a model rather than estimates. It needs {M['person_months']} person-months and about ₹{ph.total_lakh.sum() / 100:.1f} crore over 36 months, "
    f"with each phase costed by role and by purchase. The unit-economics check caught a pricing plan that would have lost money on every fleet unit and "
    f"replaced it with one in which a fleet vehicle is worth {f.ltv_to_cac} times its acquisition cost. The business becomes EBITDA-positive at month "
    f"{M['first_month_ebitda_stays_positive']} with a total funding need of about ₹{M['peak_funding_need_cr']:.0f} crore, and the biggest lever is the bill of materials. "
    "Fifteen risks have owners, mitigations and contingencies. The immediate next steps are the Week 2 fusion study, the Week 3 design and the Week 4 "
    "test strategy, which turn the first three phases of this roadmap into engineering plans.")
R.emit(section(B, "References"))
for e in ["[14]  Society of Indian Automobile Manufacturers (2025). Domestic sales data, FY2024-25.",
          "[15]  Startup India (2024). Startup India Seed Fund Scheme and Fund of Funds for Startups. Department for Promotion of Industry and Internal Trade.",
          "[16]  Central Board of Indirect Taxes and Customs. GST rate schedule for goods (18% rate applied to vehicle electronics accessories in this model).",
          f"[17]  Sharma, H. (2026). Saarthi Copilot roadmap model: resource, unit-economics, projection and risk register code. {GH}"]:
    R.p(e)
R.h1("Appendix: Model Assumptions")
rows = [[k.replace("_", " "), f"{v:,}" if isinstance(v, (int, float)) and v >= 1 else str(v)] for k, v in U.items()]
R.table(["Input", "Value"], rows, caption="Unit-economics inputs used in the model (₹ unless stated)", widths=[8.0, 4.0], font=8.5)
R.code("pip install numpy pandas matplotlib python-docx\npython src/roadmap_model.py    # writes results/ and figures/\npython src/build_report.py     # rebuilds this document")
print("words:", R.save(OUT), "figures:", R.fig_n, "tables:", R.tab_n)
