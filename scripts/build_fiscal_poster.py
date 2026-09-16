"""Editorial bubble poster: Romania's fiscal context on one page (English), same style as bvb-rallies-poster.

Synthesises every dataset behind fiscal-context.html:
- main plot: every PNRR money event as a bubble. x = date, y = € bn (log), area = € bn, colour = what happened
  (planned, received from the EU, recognised as spent, cut, suspended, lost). Open ring = not money in hand
  (a plan or a suspension); filled = money that moved or was lost.
- bottom row: deficit 2010-2025, grant absorption by payment round, the 15 plan components, public vs private wages.
- right column: numbered notes on the highlighted events.
Data: docs/fiscal-deficit-data.json (Eurostat), docs/pnrr-flows-data.json (Eurostat),
      docs/pnrr-absorption-data.json, docs/pnrr-cuts-data.json, docs/pnrr-components-data.json,
      docs/wage-gap-data.json (curated from government announcements and press).
Output: docs/fiscal-poster.html (+ optional PNG path as argv[1])."""
import json
import math
import pathlib
import sys

import plotly.graph_objects as go

sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/infodesign/scripts"))
import infodesign as ids  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
T = ids.THEMES["paper"]
BG, INK, MUTED, FAINT, RULE = T["bg"], T["ink"], T["muted"], T["faint"], T["rule"]
SERIF = "Georgia, 'Times New Roman', serif"
W, H = 1600, 1240
PLAN, RECEIVED, SPENT, CUT, LOST = "#C99A2E", "#3E7F6E", "#C8662E", "#56707F", "#9E2B2B"
GREY = "#D9CDB6"


def load(name):
    return json.loads((DOCS / f"{name}.json").read_text())


deficit = load("fiscal-deficit-data")["series"]
flows = load("pnrr-flows-data")
absorption = load("pnrr-absorption-data")
cuts = load("pnrr-cuts-data")
components = load("pnrr-components-data")
wages = load("wage-gap-data")["series"]

# ---------------- numbers (same arithmetic as build_pnrr_fragapane.py) ----------------
plan, final_plan = cuts["original_plan_eur_bn"], cuts["final_plan_eur_bn"]
grants_final, loans_final = absorption["grants_total_eur_bn"], absorption["loans_total_eur_bn"]
losses = absorption["losses"]
grants_lost, loans_lost = losses["grants_eur_bn"], losses["loans_eur_mio"] / 1000
drawn = (grants_final - grants_lost) + (loans_final - loans_lost)
final = absorption["milestones"][-1]
assert abs((grants_final - grants_lost) / grants_final * 100 - final["cumulative_grants_pct"]) < 0.1
assert abs(grants_final + loans_final - final_plan) < 0.02
assert abs(sum(c["eur_bn"] for c in components["components"]) - components["total_eur_bn_original"]) < 0.1
received_total = sum(r["grants_mio_eur"] + r["loans_mio_eur"] for r in flows["received"]) / 1000
spent_total = sum(u["capital_mio_eur"] + u["current_mio_eur"] for u in flows["use"]) / 1000
over_limit = [d for d in deficit if d["deficit_pct_gdp"] < -3]
worst = min(deficit, key=lambda d: d["deficit_pct_gdp"])
print(f"plan {plan} -> final {final_plan} (cut {plan - final_plan:.1f}); drawn {drawn:.2f} = {drawn / plan * 100:.0f}% of plan")
print(f"Eurostat received {received_total:.2f} bn, recognised spent {spent_total:.2f} bn")
print(f"deficit over 3%: {len(over_limit)} of {len(deficit)} years; worst {worst}")
print("deficit 2019-2025:", [d["deficit_pct_gdp"] for d in deficit if d["year"] >= "2019"])

# ---------------- events for the main plot ----------------
EV = []  # date, € bn, colour, filled, label, hover detail, number


def ev(date, bn, color, filled, label, detail, num=None):
    EV.append(dict(date=date, bn=bn, color=color, filled=filled, label=label, detail=detail, num=num))


ev("2021-10-15", plan, PLAN, False, "Plan approved", "€14.2bn grants + €14.9bn loans (Oct 2021)", 1)
# annual Eurostat flows sit at the end of their year; received and spent share x and differ in y
for r in flows["received"]:
    total = r["grants_mio_eur"] + r["loans_mio_eur"]
    if total > 0:
        ev(f"{r['year']}-12-15", total / 1000, RECEIVED, True, f"Received {r['year']}",
           f"EU transfers (Eurostat): €{r['grants_mio_eur']:,.0f}m grants + €{r['loans_mio_eur']:,.0f}m loans")
for u in flows["use"]:
    total = u["capital_mio_eur"] + u["current_mio_eur"]
    if total > 0:
        ev(f"{u['year']}-12-15", total / 1000, SPENT, True, f"Spent {u['year']}",
           f"Recognised as spent (Eurostat): €{u['capital_mio_eur']:,.0f}m capital + €{u['current_mio_eur']:,.0f}m current")
# events known only by year sit mid-year
CUT_DATE = {"2022": "2022-06-15", "2025": "2025-06-15", "May 2025": "2025-05-15", "May 2026": "2026-05-15",
            "Aug 2026": "2026-08-31"}
for e in cuts["events"]:
    kind = e["type"]
    if kind == "Suspended":
        ev(CUT_DATE[e["date"]], e["amount_eur_bn"], LOST, False, "Suspended", e["reason"], 3)
    elif kind == "Permanent loss":
        ev(CUT_DATE[e["date"]], e["amount_eur_bn"], LOST, True, "Lost for good", e["reason"])
    elif e["date"] == "Aug 2026":
        ev(CUT_DATE[e["date"]], e["amount_eur_bn"], LOST, True, "Salary law<br>missed", e["reason"], 4)
    else:
        ev(CUT_DATE[e["date"]], e["amount_eur_bn"], CUT, True, f"{kind} cut", e["reason"], 2 if kind == "Loans" else None)
ev("2026-08-31", final_plan, PLAN, False, "Final plan", "€13.57bn grants + €6.54bn loans after renegotiation")
ev("2026-08-31", drawn, RECEIVED, True, "Drawn", f"{final['cumulative_grants_pct']}% of grants, "
   f"{final['cumulative_loans_pct']}% of loans at closing, 31 Aug 2026", 5)

# ---------------- figure ----------------
fig = go.Figure()
MX0, MX1, MY0, MY1 = 0.215, 0.755, 0.365, 0.965
fig.update_layout(xaxis=dict(domain=[MX0, MX1], anchor="y"), yaxis=dict(domain=[MY0, MY1], anchor="x"))
sizeref = 2 * plan / 120 ** 2  # the original plan = 120 px


def diameter(bn):
    return max(math.sqrt(bn / sizeref), 7)


for filled in (False, True):  # rings under filled bubbles, so "drawn" sits inside "final plan"
    sub = [e for e in EV if e["filled"] == filled]
    fig.add_trace(go.Scatter(
        x=[e["date"] for e in sub], y=[e["bn"] for e in sub], mode="markers", showlegend=False,
        marker=dict(size=[e["bn"] for e in sub], sizemode="area", sizeref=sizeref, sizemin=7,
                    color=[e["color"] if filled else "rgba(0,0,0,0)" for e in sub], opacity=0.75 if filled else 1,
                    line=dict(color=[BG if filled else e["color"] for e in sub], width=1.5 if filled else 2.4)),
        customdata=[[e["label"].replace("<br>", " "), e["detail"]] for e in sub],
        hovertemplate="<b>%{customdata[0]}</b> · €%{y:.2f}bn<br>%{x|%b %Y}<br>%{customdata[1]}<extra></extra>"))

# labels beside bubbles; sides picked by hand where bubbles crowd (log axis: annotations take log10 y)
SIDE = {"Plan approved": "right", "Final plan": "left", "Drawn": "bottom", "Loans cut": "left", "Suspended": "left",
        "Lost for good": "left", "Salary law<br>missed": "right", "Received 2021": "left"}
for e in EV:
    r = diameter(e["bn"]) / 2
    side = SIDE.get(e["label"], "right")
    pos = dict(right=dict(xshift=r + 4, xanchor="left", align="left"),
               left=dict(xshift=-r - 4, xanchor="right", align="right"),
               top=dict(yshift=r + 4, yanchor="bottom", align="center"),
               bottom=dict(yshift=-r - 4, yanchor="top", align="center"))[side]
    num = f"<b style='color:{e['color']}'>{e['num']}.</b> " if e["num"] else ""
    amount = f"€{e['bn']:.1f}bn" if e["bn"] >= 1 else f"€{e['bn'] * 1000:,.0f}m"
    fig.add_annotation(x=e["date"], y=math.log10(e["bn"]), showarrow=False, **pos,
                       text=f"{num}<i>{e['label']}</i><br>{amount}", font=dict(family=SERIF, size=11.5, color=INK))

grid = "rgba(214,201,176,0.45)"
fig.update_xaxes(selector=dict(anchor="y"), type="date", range=["2021-01-01", "2027-03-01"], tickformat="%Y",
                 tickvals=[f"{y}-01-01" for y in range(2021, 2028)], showgrid=True, gridcolor=grid, gridwidth=0.6,
                 showline=True, linecolor=MUTED, ticks="outside", tickcolor=MUTED, zeroline=False,
                 tickfont=dict(family=SERIF, size=11, color=MUTED))
fig.update_yaxes(selector=dict(anchor="x"), type="log", range=[math.log10(0.07), math.log10(90)], showgrid=True,
                 gridcolor=grid, gridwidth=0.6, zeroline=False,
                 tickvals=[0.05, 0.1, 0.5, 1, 5, 10, 30], ticktext=["€50m", "€100m", "€500m", "€1bn", "€5bn", "€10bn", "€30bn"],
                 tickfont=dict(family=SERIF, size=11, color=MUTED))
fig.add_annotation(xref="paper", yref="paper", x=MX0 - 0.004, y=MY1 + 0.01, xanchor="right", yanchor="bottom",
                   text="<i>Amount, € (log scale)</i>", showarrow=False, font=dict(family=SERIF, size=11, color=MUTED))
fig.add_shape(type="line", xref="x", yref="paper", x0="2026-08-31", x1="2026-08-31", y0=MY0, y1=MY1,
              line=dict(color=FAINT, width=1, dash="dot"))
fig.add_annotation(xref="x", yref="paper", x="2026-08-31", y=MY1, xanchor="right", yanchor="top", xshift=-4,
                   text="<i>PNRR closes<br>31 Aug 2026</i>", showarrow=False, align="right",
                   font=dict(family=SERIF, size=10.5, color=MUTED))

# ---------------- bottom row ----------------
BY0, BY1 = 0.075, 0.29
widths = [0.25, 0.16, 0.25, 0.11]
gap = (1.0 - MX0 - sum(widths)) / 3
x0s = [MX0 + sum(widths[:i]) + gap * i for i in range(4)]


def panel(i, x_axis=None, y_axis=None, label_room=0.0):
    ax = i + 2
    base = dict(showgrid=False, zeroline=False, tickfont=dict(family=SERIF, size=10, color=MUTED))
    fig.update_layout(**{f"xaxis{ax}": {"domain": [x0s[i] + label_room, x0s[i] + widths[i]], "anchor": f"y{ax}",
                                        **base, **(x_axis or {})},
                         f"yaxis{ax}": {"domain": [BY0, BY1], "anchor": f"x{ax}", **base, **(y_axis or {})}})
    return f"x{ax}", f"y{ax}"


def caption(i, title, sub):
    fig.add_annotation(xref="paper", yref="paper", x=x0s[i], y=BY0 - 0.03, xanchor="left", yanchor="top", align="left",
                       showarrow=False, text=f"<b>{title}</b><br><span style='color:{MUTED}'>{sub}</span>",
                       font=dict(family=SERIF, size=12, color=INK))


# 6. deficit
xa, ya = panel(0, x_axis=dict(tickvals=[deficit[0]["year"], "2020", deficit[-1]["year"]], ticks=""),
               y_axis=dict(visible=False, range=[min(d["deficit_pct_gdp"] for d in deficit) * 1.15, 0.6]))
fig.add_trace(go.Bar(x=[d["year"] for d in deficit], y=[d["deficit_pct_gdp"] for d in deficit], xaxis=xa, yaxis=ya,
                     showlegend=False, marker=dict(color=[LOST if d["deficit_pct_gdp"] < -3 else GREY for d in deficit]),
                     text=[f"{d['deficit_pct_gdp']:.1f}".replace("-", "−") if d["deficit_pct_gdp"] < -3 else ""
                           for d in deficit], textposition="outside",
                     textfont=dict(family=SERIF, size=9.5, color=MUTED), cliponaxis=False,
                     hovertemplate="%{x}: %{y:.1f}% of GDP<extra></extra>"))
fig.add_shape(type="line", xref=f"{xa} domain", yref=ya, x0=0, x1=1, y0=-3, y1=-3, line=dict(color=INK, width=0.8, dash="dot"))
fig.add_annotation(xref=f"{xa} domain", yref=ya, x=1, y=-3, xanchor="left", yanchor="middle", text="EU 3%",
                   showarrow=False, font=dict(family=SERIF, size=10, color=INK))
caption(0, "6. Budget deficit, % of GDP",
        f"above the EU 3% limit in {len(over_limit)} of {len(deficit)} years; −{abs(worst['deficit_pct_gdp'])}% in 2020 and 2024")

# grant absorption by payment round
ms = absorption["milestones"]
short = ["Approved", "P1", "P2", "P3", "Bolojan", "P4", "P5", "Final"]
assert len(short) == len(ms)
xa, ya = panel(1, x_axis=dict(tickangle=0, tickfont=dict(family=SERIF, size=9.5, color=MUTED)),
               y_axis=dict(visible=False, range=[0, 112]))
fig.add_trace(go.Bar(x=short, y=[m["cumulative_grants_pct"] for m in ms], xaxis=xa, yaxis=ya, showlegend=False,
                     marker=dict(color=[PLAN if "Ciolacu" in m["label"] or "Iohannis" in m["label"] else RECEIVED for m in ms]),
                     text=[f"{m['cumulative_grants_pct']:.0f}%" for m in ms], textposition="outside", cliponaxis=False,
                     textfont=dict(family=SERIF, size=10, color=MUTED),
                     customdata=[m["label"] for m in ms], hovertemplate="%{customdata}: %{y}% of grants<extra></extra>"))
caption(1, "Grants drawn, cumulative",
        f"<span style='color:{PLAN}'>■</span> Ciolacu  <span style='color:{RECEIVED}'>■</span> Bolojan · "
        f"{final['cumulative_grants_pct']}% at closing")

# components (original 2021 plan)
comps = sorted(components["components"], key=lambda c: c["eur_bn"])
xa, ya = panel(2, x_axis=dict(visible=False, range=[0, max(c["eur_bn"] for c in comps) * 1.4]),
               y_axis=dict(tickfont=dict(family=SERIF, size=9.5, color=INK), ticks="", automargin=False), label_room=0.115)
fig.add_trace(go.Bar(y=[c["name"] for c in comps], x=[c["eur_bn"] for c in comps], orientation="h", xaxis=xa, yaxis=ya,
                     showlegend=False, marker=dict(color=[PLAN if c is comps[-1] else "#DCC79A" for c in comps]),
                     text=[f"€{c['eur_bn']:.2f}bn" for c in comps], textposition="outside", cliponaxis=False,
                     textfont=dict(family=SERIF, size=9.5, color=MUTED), hovertemplate="%{y}: €%{x}bn<extra></extra>"))
caption(2, "Where the 2021 plan was meant to go",
        f"15 components, €{components['total_eur_bn_original']}bn; transport alone {comps[-1]['eur_bn'] / plan * 100:.0f}%")

# wages
xa, ya = panel(3, x_axis=dict(ticks=""), y_axis=dict(visible=False, range=[0, max(w["public_net_ron"] for w in wages) * 1.22]))
for key, color, name in (("public_net_ron", LOST, "public"), ("private_net_ron", GREY, "private")):
    fig.add_trace(go.Bar(x=[str(w["year"]) for w in wages], y=[w[key] for w in wages], xaxis=xa, yaxis=ya, name=name,
                         showlegend=False, marker=dict(color=color), offsetgroup=name,
                         text=[f"{w[key]:,}" for w in wages], textposition="outside", cliponaxis=False,
                         textfont=dict(family=SERIF, size=9.5, color=MUTED),
                         hovertemplate=f"%{{x}} {name}: %{{y:,}} RON net<extra></extra>"))
caption(3, "7. Net wage, RON",
        f"<span style='color:{LOST}'>■</span> public <span style='color:{GREY}'>■</span> private<br>"
        f"public +{wages[-1]['gap_pct']:.0f}% in {wages[-1]['year']}")

# ---------------- left column ----------------
fig.add_annotation(xref="paper", yref="paper", x=0, y=0.985, xanchor="left", yanchor="top", align="left", showarrow=False,
                   text="Romania's<br>recovery<br>money", font=dict(family=ids.SERIF, size=40, color=LOST))
intro = (f"Every PNRR money event, 2021–2026:<br>what was planned, received, spent,<br>cut and lost.<br><br>"
         f"<b>Of the €{plan}bn planned in 2021,<br>about €{drawn:.1f}bn was drawn</b> —<br>"
         f"{drawn / plan * 100:.0f}% of the original plan —<br>"
         f"while the deficit stayed above 3%<br>of GDP every year since 2019.")
fig.add_annotation(xref="paper", yref="paper", x=0, y=0.8, xanchor="left", yanchor="top", align="left", showarrow=False,
                   text=intro, font=dict(family=SERIF, size=13, color=INK))
fig.add_annotation(xref="paper", yref="paper", x=0, y=0.6, xanchor="left", yanchor="top", align="left", showarrow=False,
                   text="<b>How to read it?</b>", font=dict(family=SERIF, size=16, color=LOST))
fig.add_shape(type="line", xref="paper", yref="paper", x0=0, x1=0.105, y0=0.578, y1=0.578, line=dict(color=LOST, width=1))
fig.add_annotation(xref="paper", yref="paper", x=0, y=0.566, xanchor="left", yanchor="top", align="left", showarrow=False,
                   font=dict(family=SERIF, size=12, color=MUTED),
                   text="Each bubble is one amount of money.<br>Height and area both show €.<br>"
                        "Numbers link to the notes on<br>the right and the panels below.")
fig.update_layout(xaxis8=dict(domain=[0, 0.19], anchor="y8", visible=False, range=[0, 10]),
                  yaxis8=dict(domain=[0.37, 0.49], anchor="x8", visible=False, range=[-0.5, 6.5]))
legend = [(RECEIVED, True, "Received from the EU / drawn"), (SPENT, True, "Recognised as spent"),
          (CUT, True, "Cut from the plan"), (LOST, True, "Lost"), (LOST, False, "Open ring = suspended,<br>not yet lost"),
          (PLAN, False, "Open ring = plan size")]
for k, (color, filled, text) in enumerate(legend):
    y = 6 - k * 1.2
    fig.add_trace(go.Scatter(x=[1], y=[y], xaxis="x8", yaxis="y8", mode="markers", hoverinfo="skip", showlegend=False,
                             marker=dict(size=13, color=color if filled else "rgba(0,0,0,0)", opacity=0.8 if filled else 1,
                                         line=dict(color=color, width=0 if filled else 2))))
    fig.add_annotation(xref="x8", yref="y8", x=2.4, y=y, xanchor="left", showarrow=False, align="left", text=text,
                       font=dict(family=SERIF, size=11.5, color=INK))

# ---------------- right column: notes ----------------
ev_by_num = {e["num"]: e for e in EV if e["num"]}
susp = next(e for e in cuts["events"] if e["type"] == "Suspended")
perm = next(e for e in cuts["events"] if e["type"] == "Permanent loss")
loan_cut = next(e for e in cuts["events"] if e["type"] == "Loans")


def items(e):
    short = {"AMEPIP operationalization": "state-company watchdog (AMEPIP)",
             "State-company administrator appointments": "state-company board appointments",
             "Special/magistrate pensions reform": "special pensions reform"}
    return "<br>".join(f"€{b['amount_eur_mio']:,.0f}m {short.get(b['label'].split(' (')[0], b['label'])}"
                       for b in e["breakdown"])


notes = [
    (PLAN, 1, "Plan approved, Oct 2021", f"€{plan}bn: €14.2bn grants<br>+ €14.9bn loans"),
    (CUT, 2, f"Loans cut, {loan_cut['date']}", f"−€{loan_cut['amount_eur_bn']}bn: projects that could not<br>"
                                                f"finish by Aug 2026 dropped;<br>some moved to cohesion funds"),
    (LOST, 3, f"Payment suspended, {susp['date']}", f"€{susp['amount_eur_bn'] * 1000:.0f}m over 3 missed milestones:<br>"
                                                    f"<span style='color:{MUTED}'>{items(susp)}</span><br>"
                                                    f"€{perm['amount_eur_bn'] * 1000:.0f}m of it lost for good, {perm['date']}"),
    (LOST, 4, "Salary law missed, Aug 2026", f"€{losses['salary_law_milestone_eur_mio']}m of the ~€{losses['total_eur_bn']}bn<br>"
                                              "not drawn at closing"),
    (RECEIVED, 5, "Closing, 31 Aug 2026", f"Plan €{final_plan}bn; drawn {final['cumulative_grants_pct']}% of grants,<br>"
                                          f"{final['cumulative_loans_pct']}% of loans ≈ €{drawn:.1f}bn"),
]  # notes 6 and 7 (deficit, wages) live in the panel captions
ny = 0.975
for color, n, head, body in notes:
    fig.add_annotation(xref="paper", yref="paper", x=0.83, y=ny, xanchor="left", yanchor="top", align="left", showarrow=False,
                       text=f"<b style='color:{color}'>{n}.</b><br><b>{head}</b><br>{body}",
                       font=dict(family=SERIF, size=11.5, color=INK))
    ny -= 0.09 + 0.022 * body.count("<br>")

src = ("Annual Eurostat flows are placed at the end of their year; events dated only by year, mid-year.<br>"
       "Source: Eurostat (deficit gov_10dd_edpt1; PNRR transfers gov_rrf_fa and use gov_rrf_use). Plan, absorption, cuts, "
       "losses and wages curated from government announcements and press (INS for wages).<br>Cut and loss events overlap "
       "and are not a waterfall: the May 2026 loss is part of the May 2025 suspension. Components are the original 2021 plan, "
       "not final spending. 'Drawn' = final envelope minus reported losses.")
fig.add_annotation(xref="paper", yref="paper", x=MX0, y=-0.005, xanchor="left", yanchor="top", align="left",
                   showarrow=False, text=src, font=dict(family=ids.SANS, size=10.5, color=FAINT))

ids.apply_theme(fig, "paper", header="none", width=W, height=H)
fig.update_layout(margin=dict(l=60, r=50, t=40, b=60), bargap=0.18, barmode="group", hovermode="closest")

if __name__ == "__main__":
    ids.export(fig, "fiscal-poster", DOCS, targets=("html",))
    if len(sys.argv) > 1:
        fig.write_image(sys.argv[1], scale=1)
    print("wrote docs/fiscal-poster.html")
