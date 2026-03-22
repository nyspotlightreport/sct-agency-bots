import os,re
AGENTS=os.path.join(os.path.dirname(__file__),"agents") if os.path.exists("agents") else "C:\\Users\\S\\sct-agency-bots\\agents"
os.chdir("C:\\Users\\S\\sct-agency-bots")
DIRECTORS={
    "nina_caldwell_strategist.py":{"id":"nina_caldwell","persp":["buffett_roic","thiel_power_law","porter_value_chain","kaplan_scorecard"],"chain":3,"rank":"roi_multiple"},
    "elliot_shaw_marketing.py":{"id":"elliot_shaw","persp":["hormozi_offer","ogilvy_brand","cialdini_persuasion","brunson_funnel"],"chain":3,"rank":"conversion_rate"},
    "rowan_blake_bizdev.py":{"id":"rowan_blake","persp":["thiel_network","blue_ocean","hoffman_blitz","ansoff_growth"],"chain":3,"rank":"partnership_revenue"},
    "parker_hayes_product.py":{"id":"parker_hayes","persp":["jobs_jtbd","christensen_disruption","hormozi_offer","moore_chasm"],"chain":3,"rank":"conversion_times_price"},
    "casey_lin_it.py":{"id":"casey_lin","persp":["sre_error_budgets","chaos_engineering","zero_trust","cost_opt"],"chain":2,"rank":"system_reliability"},
    "jordan_wells_operations.py":{"id":"jordan_wells","persp":["goldratt_constraints","lean_six_sigma","toyota_production","deming_pdca"],"chain":3,"rank":"throughput"},
    "cameron_reed_content.py":{"id":"cameron_reed","persp":["seo_authority","viral_social","email_nurture","repurpose_10x"],"chain":3,"rank":"seo_conversion"},
    "vivian_cole_pr.py":{"id":"vivian_cole","persp":["earned_media","thought_leadership","crisis_prevention","authority_build"],"chain":3,"rank":"media_pickup"},
    "drew_sinclair_analytics.py":{"id":"drew_sinclair","persp":["pareto_80_20","cohort_analysis","bayesian_updating","causal_inference"],"chain":3,"rank":"decision_quality"},
    "blake_sutton_finance.py":{"id":"blake_sutton","persp":["buffett_value","dalio_allweather","graham_safety","unit_economics"],"chain":2,"rank":"risk_adjusted_return"},
    "taylor_grant_hr.py":{"id":"taylor_grant","persp":["grove_high_output","radical_candor","right_people_bus","ai_workforce_opt"],"chain":2,"rank":"workforce_roi"},
    "hayden_cross_qc.py":{"id":"hayden_cross","persp":["deming_quality","six_sigma","jobs_quality_bar","pixar_iteration"],"chain":3,"rank":"quality_revenue_ready"},
}
patched=0
for fname,cfg in DIRECTORS.items():
    fpath=os.path.join("agents",fname)
    if not os.path.exists(fpath):
        print(f"  SKIP {fname}");continue
    with open(fpath,"r",encoding="utf-8") as f: code=f.read()
    if "SuperDirector" in code:
        print(f"  ALREADY {fname}");continue
    # Add import after existing imports
    inject_import="from agents.supercore import SuperDirector,pushover as super_push\n"
    if "import os" in code:
        code=code.replace("import os",inject_import+"import os",1)
    else:
        code=inject_import+code
    # Add execute_super function at end
    persp_str=str(cfg["persp"])
    inject_fn=f'''

# ═══ SUPERCORE PARALLELISM WIRING ═══
def execute_super(task=None):
    """Fan-out parallel reasoning + generate-then-rank + chain-of-thought."""
    class Dir(SuperDirector):
        DIRECTOR_ID="{cfg['id']}"
        DIRECTOR_NAME="{cfg['id'].replace("_"," ").title()}"
        DIRECTOR_TITLE="Director"
        PERSPECTIVES={persp_str}
        DIRECTOR_PROMPT=SYSTEM if 'SYSTEM' in dir() else "You are a director."
    d=Dir()
    if not task:
        task="Daily autonomous assessment: 1.Highest-leverage cash action in 24h? 2.Wasted tool/integration? 3.Cross-dept synergy? 4.Grade your domain A+ to F."
    return d.execute_full(task,parallel_perspectives={persp_str},chain_steps={cfg['chain']},rank_criteria="{cfg['rank']}")

if __name__=="__main__":
    import sys as _s
    if len(_s.argv)>1 and _s.argv[1]=="--super":
        t=" ".join(_s.argv[2:]) if len(_s.argv)>2 else None
        r=execute_super(t)
        print(f"Grade:{{r.get('grade','?')}}\\n{{r.get('final_output','')[:1000]}}")
    else:
        run()
'''
    # Only add if not already present
    if "execute_super" not in code:
        # Replace the existing if __name__ block
        code=re.sub(r'\nif __name__\s*==\s*"__main__".*$',inject_fn,code,flags=re.DOTALL)
        if "execute_super" not in code:  # fallback: just append
            code+=inject_fn
    with open(fpath,"w",encoding="utf-8") as f: f.write(code)
    patched+=1
    print(f"  WIRED {fname}")
print(f"\nPatched {patched}/{len(DIRECTORS)} directors")
