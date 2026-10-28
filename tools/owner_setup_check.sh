#!/usr/bin/env bash
# Confirm each owner setup item (infra/OWNER-SETUP.md) without printing any secret, and tick the items that pass.
#   tools/owner_setup_check.sh           check and tick
#   tools/owner_setup_check.sh --dry     check only
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "$0")/.."
SECRETS="$HOME/.argonia/secrets.env"
pass=(); fail=()
ok()  { echo "  ok    $1"; pass+=("$2"); }
bad() { echo "  todo  $1"; fail+=("$2"); }
na()  { echo "  ?     $1"; }

has_secret() { [ -f "$SECRETS" ] && grep -q -E "^[[:space:]]*(export[[:space:]]+)?$1=." "$SECRETS"; }

echo "Owner setup check"
if [ -f "$SECRETS" ] && [ "$(stat -c %a "$SECRETS")" = 600 ]; then
  has_secret NEXUS_API_KEY && ok "secrets.env (mode 600) has NEXUS_API_KEY" "**The secrets file" \
    || bad "NEXUS_API_KEY missing from secrets.env" "**The secrets file"
else
  bad "~/.argonia/secrets.env missing or not mode 600" "**The secrets file"
fi
for k in R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_ENDPOINT OLD_REPO_TOKEN FAL_KEY; do
  has_secret "$k" && echo "  ok    $k (0.1)" || echo "  later $k (asked for in 0.1)"
done

if gh auth status 2>&1 | grep -q "Token scopes:.*'repo'.*'workflow'\|Token scopes:.*'workflow'.*'repo'"; then
  ok "gh signed in with repo and workflow scopes" "**Claude Code and GitHub"
else
  bad "gh needs the repo and workflow scopes (gh auth refresh -s workflow)" "**Claude Code and GitHub"
fi
gh variable list -R jtattersall09403/skyrim-argonia 2>/dev/null | grep -q '^AWS_WAKE_ROLE_ARN' \
  && echo "  ok    repo variable AWS_WAKE_ROLE_ARN" || echo "  todo  repo variable AWS_WAKE_ROLE_ARN (step 6)"

if aws sts get-caller-identity --query Arn --output text 2>/dev/null | grep -q 'assumed-role/argonia-build-ssm/'; then
  echo "  ok    AWS role argonia-build-ssm"
  aws ec2 describe-instances --region eu-west-2 --max-items 1 >/dev/null 2>&1 \
    && echo "  ok    agent policy: ec2:Describe" || echo "  todo  agent policy argonia-agent (step 5)"
  aws ce get-cost-and-usage --time-period "Start=$(date +%Y-%m-01),End=$(date -d tomorrow +%F)" \
    --granularity MONTHLY --metrics UnblendedCost >/dev/null 2>&1 \
    && echo "  ok    agent policy: Cost Explorer read" || echo "  todo  agent policy: Cost Explorer read (step 5)"
  q=$(aws service-quotas get-service-quota --region eu-west-2 --service-code ec2 --quota-code L-3819A6DF \
      --query Quota.Value --output text 2>/dev/null || echo 0)
  awk -v q="$q" 'BEGIN{exit !(q>=4)}' && echo "  ok    G spot quota $q vCPUs" || echo "  todo  G spot quota $q vCPUs (needs 4+)"
else
  echo "  todo  AWS CLI or the instance role is not working"
fi
na "idle backstop alarm argonia-build-idle-stop: the agent policy cannot read alarms; the owner confirms it"

for d in skyrimse dsr; do
  [ -d "$HOME/games/$d" ] && echo "  ok    ~/games/$d ($(du -sh "$HOME/games/$d" | cut -f1))" || echo "  todo  ~/games/$d (step 7)"
done

if [ "${1:-}" != "--dry" ] && [ ${#pass[@]} -gt 0 ]; then
  for item in "${pass[@]}"; do
    python3 -I - "infra/OWNER-SETUP.md" "$item" <<'EOF'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); key = "- [ ] " + sys.argv[2]
text = p.read_text()
if key in text:
    p.write_text(text.replace(key, "- [x] " + sys.argv[2], 1))
    print("  ticked:", sys.argv[2].strip("*"))
EOF
  done
fi
[ ${#fail[@]} -eq 0 ]
