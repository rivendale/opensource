#!/usr/bin/env python3
"""Offline gate evaluation and reviewed-source secret tripwires. No live key/model call."""
import argparse,ast,hashlib,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REVIEWER='682e67dd0722ec59ca20843eead86a4857e03ad6'
TREE='e54306fa18285f087f641dcc8ecb64cbdb9a0df8'
EXPECTED='994c3c8640cf828a5e728ee764bfe8bec9a5ad7f642772baf7e05ab12eede8ce'
def gate(expr,enabled=None,fork=False,name='example/repository',actor='human',author='human'):
 values={'github.event.pull_request.head.repo.full_name':name,'github.event.pull_request.head.repo.fork':fork,'github.event.pull_request.user.login':author,'vars.AI_REDTEAM_ENABLED':enabled,'github.repository':'example/repository','github.actor':actor}
 for key in sorted(values,key=len,reverse=True):expr=expr.replace(key,repr(values[key]))
 expr=expr.replace('&&','and').replace('== false','== False')
 node=ast.parse(expr,mode='eval')
 assert all(isinstance(n,(ast.Expression,ast.BoolOp,ast.And,ast.Compare,ast.Eq,ast.NotEq,ast.Constant)) for n in ast.walk(node))
 return eval(compile(node,'fixed-workflow-gate','eval'),{'__builtins__':{}},{})
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);args=parser.parse_args()
 text=(ROOT/'.github/workflows/ai-redteam-pr-review.yml').read_text()
 assert hashlib.sha256(text.encode()).hexdigest()==EXPECTED,'secret boundary changed; independent read required'
 expr=re.search(r'^    if: \$\{\{ (.+) \}\}$',text,re.M)[1]
 assert gate(expr,'true')
 for enabled in (None,'','false','TRUE'):assert not gate(expr,enabled)
 assert not gate(expr,'true',True);assert not gate(expr,'true',True,'elsewhere/fork')
 assert not gate(expr,'true',False,'elsewhere/repository')
 assert not gate(expr,'true',actor='dependabot[bot]');assert not gate(expr,'true',author='dependabot[bot]')
 assert ': write' not in text and 'pull-requests: read' in text and 'contents: read' in text
 assert 'ref: ${{ github.event.pull_request.base.sha }}' in text
 assert 'pull_request.head.sha }}' not in text and text.count('persist-credentials: false')==2
 assert re.findall(r'^\s*run: (.+)',text,re.M)==['python3 .ai-redteam-review/tools/pr_review_action.py']
 assert re.findall(r'^\s*uses: (.+)',text,re.M)==['actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0']*2
 assert text.count('secrets.AI_REDTEAM_MODEL_KEY')==1 and REVIEWER in text
 tree=subprocess.check_output(['git','-C',str(args.source),'rev-parse','HEAD^{tree}'],text=True).strip();assert tree==TREE,'reviewed-source tree differs'
 # These tests use a transport spy and a dict that raises on token/key access for denied inputs.
 for name in ('test_pr_review_action.py','test_pr_review_errors.py'):
  subprocess.run([sys.executable,str(args.source/'tests'/name)],check=True)
 print('Workflow: eligible positive and 9 denial controls; reviewed-source 13 boundary + 14 diagnostic tests pass')
 return 0
if __name__=='__main__':raise SystemExit(main())
