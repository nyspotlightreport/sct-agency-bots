import os, re, subprocess
AGENTS = r'C:\Users\S\sct-agency-bots\agents'
DIRECTORS = {
    'nina_caldwell_strategist.py': ['buffett_roic','thiel_power_law','porter_value_chain','kaplan_scorecard'],
    'elliot_shaw_marketing.py': ['hormozi_offer','ogilvy_brand','cialdini_persuasion','brunson_funnel'],
    'rowan_blake_bizdev.py': ['thiel_network','blue_ocean','hoffman_blitz','ansoff_growth'],
    'parker_hayes_product.py': ['jobs_jtbd','christensen_disruption','hormozi_offer','moore_chasm'],
    'casey_lin_it.py': ['sre_error_budgets','chaos_engineering','zero_trust','cost_opt'],
    'jordan_wells_operations.py': ['goldratt_constraints','lean_six_sigma','toyota_production','deming_pdca'],
    'cameron_reed_content.py': ['seo_authority','viral_social','email_nurture','repurpose_10x'],
    'vivian_cole_pr.py': ['earned_media','thought_leadership','crisis_prevention','authority_build'],
    'drew_sinclair_analytics.py': ['pareto_80_20','cohort_analysis','bayesian_updating','causal_inference'],
    'blake_sutton_finance.py': ['buffett_value','dalio_allweather','graham_safety','unit_economics'],
    'taylor_grant_hr.py': ['grove_high_output','radical_candor','right_people_bus','ai_workforce_opt'],
    'hayden_cross_qc.py': ['deming_quality','six_sigma','jobs_quality_bar','pixar_iteration'],
}
patched = 0
for fname, persp in DIRECTORS.items():
    fpath = os.path.join(AGENTS, fname)
    if not os.path.exists(fpath):
        print(f'SKIP {fname}'); continue
    with open(fpath, 'r', encoding='utf-8') as f:
        code = f.read()
    if 'execute_super' in code:
        print(f'ALREADY {fname}'); patched += 1; continue
    imp = 'from agents.supercore import SuperDirector, pushover as super_push\n'
    if imp not in code:
        code = imp + code
    did = fname.replace('.py','')
    dname = did.replace('_',' ').title()
    fn = f'''

# === SUPERCORE PARALLELISM ===
def execute_super(task=None):
    class Dir(SuperDirector):
        DIRECTOR_ID = "{did}"
        DIRECTOR_NAME = "{dname}"
        DIRECTOR_TITLE = "Director"
        PERSPECTIVES = {persp}
        DIRECTOR_PROMPT = SYSTEM if 'SYSTEM' in dir() else "Director"
    d = Dir()
    if not task:
        task = "Daily: 1.Highest-leverage cash action 24h? 2.Wasted integration? 3.Cross-dept synergy? 4.Grade A+ to F."
    return d.execute_full(task, parallel_perspectives={persp}, chain_steps=3, rank_criteria="revenue_impact")

if __name__ == "__main__":
    import sys as _s
    if len(_s.argv) > 1 and _s.argv[1] == "--super":
        t = " ".join(_s.argv[2:]) if len(_s.argv) > 2 else None
        r = execute_super(t)
        print("Grade:", r.get("grade", "?"))
    else:
        run()
'''
    code = re.sub(r'\nif __name__\s*==\s*["\']__main__["\'].*$', '', code, flags=re.DOTALL)
    code += fn
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(code)
    patched += 1
    print(f'WIRED {fname}')
print(f'\nTotal: {patched}/12 wired')
os.chdir(r'C:\Users\S\sct-agency-bots')
subprocess.run(['git','add','-A'], capture_output=True)
r = subprocess.run(['git','commit','-m','wire: 12 directors supercore parallelism'], capture_output=True, text=True)
print(r.stdout[:200] if r.stdout else r.stderr[:200])
r2 = subprocess.run(['git','push','origin','main'], capture_output=True, text=True)
print('PUSHED' if r2.returncode == 0 else r2.stderr[:200])
