#!/usr/bin/env python3
"""Print the default model/rate fragment for a NEW studio plan. No execution or file writes."""
import argparse,json
from cache_api import DEFAULT_NEW_MODEL,RATES,RATES_DATE,RATES_DATES,RATES_SOURCE

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--model',default=DEFAULT_NEW_MODEL,choices=sorted(RATES))
 args=parser.parse_args()
 print(json.dumps({'model':args.model,'rates_date':RATES_DATES.get(args.model,RATES_DATE),'rates_source':RATES_SOURCE},indent=2))
 return 0
if __name__=='__main__':raise SystemExit(main())
