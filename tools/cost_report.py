#!/usr/bin/env python3
"""AWS month-to-date cost (Cost Explorer, by service, top 8 + total), every Argonia machine (build VM and each game
machine argonia-play, argonia-play-N) with its state and price per hour, and Claude usage. Always exits 0."""
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


GP3_GB_MONTH = 0.0928  # eu-west-2 gp3, USD per GiB-month (AWS price list, 2026-10)
IPV4_HOUR = 0.005  # public IPv4 while attached
PLAY_BAR = 0.50  # the owner's ceiling for a game machine, $/h (owner-brief 2026-10-31, the machine bar)


def machines() -> None:
    """Each project=argonia machine: state, type, current spot price, disk; the standing cost of the stopped ones."""
    try:
        import boto3
        ec2 = boto3.client("ec2", region_name="eu-west-2")
        rows = []
        for res in ec2.describe_instances(Filters=[{"Name": "tag:project", "Values": ["argonia"]},
                                                   {"Name": "instance-state-name",
                                                    "Values": ["pending", "running", "stopping", "stopped"]}])["Reservations"]:
            for i in res["Instances"]:
                name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), i["InstanceId"])
                vols = [m["Ebs"]["VolumeId"] for m in i.get("BlockDeviceMappings", []) if "Ebs" in m]
                gib = sum(v["Size"] for v in ec2.describe_volumes(VolumeIds=vols)["Volumes"]) if vols else 0
                os_ = "Windows" if i.get("Platform") == "windows" else "Linux/UNIX"
                hist = ec2.describe_spot_price_history(
                    InstanceTypes=[i["InstanceType"]], ProductDescriptions=[os_],
                    AvailabilityZone=i["Placement"]["AvailabilityZone"], MaxResults=1)["SpotPriceHistory"]
                price = float(hist[0]["SpotPrice"]) if hist else float("nan")
                rows.append((name, i["State"]["Name"], i["InstanceType"], price, gib))
    except Exception as e:  # noqa: BLE001 -- a report line, never a crash
        print(f"Machines: unavailable ({type(e).__name__})")
        return
    print("Machines (spot $/h now + IPv4; disk $/month whether running or not)")
    disks = 0.0
    for name, state, typ, price, gib in sorted(rows):
        disk = gib * GP3_GB_MONTH
        disks += disk
        over = name.startswith("argonia-play") and price + IPV4_HOUR > PLAY_BAR
        print(f"  {name:<16}{state:<9}{typ:<16}{price + IPV4_HOUR:6.3f}/h  {gib:4d} GiB {disk:6.2f}/month"
              + (f"  OVER ${PLAY_BAR:.2f}/h: move with infra/gpu-box/play_move.sh (1.8)" if over else ""))
    print(f"  {'disks':<41}{disks:22.2f}/month")


def claude() -> None:
    script = Path(__file__).resolve().parent.parent / "tooling" / "session_tokens.py"
    if not script.exists():
        print("Claude usage: tooling/session_tokens.py not present yet")
        return
    r = subprocess.run([sys.executable, str(script), "--brief"], capture_output=True, text=True, timeout=120)
    print((r.stdout or r.stderr).strip() or "Claude usage: no output")


if __name__ == "__main__":
    aws()
    machines()
    claude()
