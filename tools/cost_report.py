#!/usr/bin/env python3
"""AWS month-to-date cost (Cost Explorer, by service, top 8 + total) and Claude usage. Always exits 0."""
import datetime as dt
import subprocess
import sys
from pathlib import Path


def aws() -> None:
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        print("AWS cost: boto3 missing (run infra/build-vm/setup.sh)")
        return
    today = dt.date.today()
    start = today.replace(day=1)
    end = today + dt.timedelta(days=1)  # End is exclusive
    try:
        ce = boto3.client("ce", region_name="us-east-1")
        rows = {}
        kw = dict(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Granularity="MONTHLY", Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        while True:
            r = ce.get_cost_and_usage(**kw)
            for period in r["ResultsByTime"]:
                for g in period["Groups"]:
                    rows[g["Keys"][0]] = rows.get(g["Keys"][0], 0.0) + float(g["Metrics"]["UnblendedCost"]["Amount"])
            if not r.get("NextPageToken"):
                break
            kw["NextPageToken"] = r["NextPageToken"]
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("AccessDeniedException", "AccessDenied", "UnauthorizedOperation"):
            print("AWS cost: no permission for Cost Explorer (ce:GetCostAndUsage) on this role")
        else:
            print(f"AWS cost: unavailable ({code})")
        return
    except BotoCoreError as e:
        print(f"AWS cost: unavailable ({type(e).__name__})")
        return
    print(f"AWS month-to-date {start}..{today} (USD, unblended)")
    for name, cost in sorted(rows.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  {name:<46}{cost:9.2f}")
    print(f"  {'TOTAL':<46}{sum(rows.values()):9.2f}")


def claude() -> None:
    script = Path(__file__).resolve().parent.parent / "tooling" / "session_tokens.py"
    if not script.exists():
        print("Claude usage: tooling/session_tokens.py not present yet")
        return
    r = subprocess.run([sys.executable, str(script), "--brief"], capture_output=True, text=True, timeout=120)
    print((r.stdout or r.stderr).strip() or "Claude usage: no output")


if __name__ == "__main__":
    aws()
    claude()
