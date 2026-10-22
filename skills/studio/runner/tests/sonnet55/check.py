#!/usr/bin/env python3
"""Offline planning/accounting checks; no credential or provider."""
import importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import cache_api
assert cache_api.RATES['claude-sonnet-5-5']==(2,2.5,4,.10,10)
u=cache_api.native_usage({'input_tokens':1000000,'output_tokens':1000000,'cache_creation_input_tokens':2000000,'cache_read_input_tokens':1000000,'cache_creation':{'ephemeral_5m_input_tokens':1000000,'ephemeral_1h_input_tokens':1000000}})
assert cache_api.estimate_cost(u,'claude-sonnet-5-5')==18.6
receipt=cache_api.receipt(u,'claude-sonnet-5-5');assert receipt['rates_date']=='2026-10-22';assert receipt['rates_source']=='https://platform.claude.com/docs/en/about-claude/pricing'
old=cache_api.receipt(u,'claude-sonnet-4-5-20250929');assert old['rates_date']=='2026-10-16'
assert cache_api.estimate_cost(u,'unknown-model-fixture') is None
p=subprocess.run([sys.executable,str(ROOT/'plan.py')],capture_output=True,text=True,check=True);plan=json.loads(p.stdout)
assert plan['model']=='claude-sonnet-5-5' and plan['rates_date']=='2026-10-22'
p=subprocess.run([sys.executable,str(ROOT/'plan.py'),'--model','unknown-model-fixture'],capture_output=True,text=True);assert p.returncode!=0 and not p.stdout
p=subprocess.run([sys.executable,str(ROOT/'plan.py'),'--model','claude-sonnet-4-5-20250929'],capture_output=True,text=True,check=True);assert json.loads(p.stdout)['model']=='claude-sonnet-4-5-20250929'
print('Sonnet 5.5 five-column accounting, planning default, explicit old model and unknown refusal pass')
