"""Manually attest fresh provider balance/prices; never automatically renew."""
import argparse
import json
import time
from pathlib import Path

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--credit', type=float, required=True)
    p.add_argument('--input-price', type=float, required=True)
    p.add_argument('--output-price', type=float, required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--verified-now', action='store_true', required=True)
    a = p.parse_args()
    import math
    if (not all(math.isfinite(v) for v in [a.credit,a.input_price,a.output_price])
        or a.credit < .5 or not 0 <= a.input_price <= .06
        or not 0 <= a.output_price <= .24 or not a.model.startswith('nvidia/')):
        p.error('Verified credit or price is outside the free-only limits')
    target = Path('.runtime/free-credit-session.json')
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({'verified_at':time.time(),'model':a.model,
        'free_credit_usd':a.credit,'input_usd_per_million':a.input_price,
        'output_usd_per_million':a.output_price,'reserved_calls':0}))
    print('Two-request allowance created; expires in ten minutes. No API call made.')
