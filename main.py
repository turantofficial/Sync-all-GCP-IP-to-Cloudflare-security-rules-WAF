import os
import json
import requests
from google.cloud import secretmanager
from googleapiclient import discovery
from flask import jsonify

def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ.get("CF_SECRET_PROJECT", os.environ["GCP_PROJECT"])
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_external_ips():
    projects = [
        "projectA",
        "projectB",
        "projectC",
    ]

    compute = discovery.build("compute", "v1")
    all_ips = []

    for project in projects:
        try:
            print(f"🔍 Checking project: {project}")
            req = compute.addresses().aggregatedList(project=project, filter="addressType=EXTERNAL")
            while req is not None:
                res = req.execute()
                for _, region_data in res.get("items", {}).items():
                    for addr in region_data.get("addresses", []):
                        ip = addr.get("address")
                        if ip:
                            all_ips.append(ip)
                req = compute.addresses().aggregatedList_next(previous_request=req, previous_response=res)
        except Exception as e:
            print(f" Error in {project}: {e}")

    # Include office IPs (IPv4 + IPv6)
    all_ips.extend([
        "10.10.10.10",
        "2400:1002:0201:22c::",
        "2400:1002:0201:22c:"
    ])
    all_ips = sorted(set(all_ips))
    print(f" Total external IPs (including office): {len(all_ips)}")
    return all_ips


def update_zone(label, zone_id, ruleset_id, rule_id, cf_api_token, ips):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets/{ruleset_id}/rules/{rule_id}"
    expression = f"(ip.src in {{{' '.join(ips)}}})"

    data = {
        "action": "skip",
        "action_parameters": {
            "phases": [
                "http_request_sbfm",
                "http_request_firewall_managed",
                "http_ratelimit"
            ],
            "products": ["waf", "rateLimit"],
            "ruleset": "current"
        },
        "description": f"Office und GCP IPs (auto-sync) [{label}]",
        "enabled": True,
        "expression": expression
    }

    headers = {"Authorization": f"Bearer {cf_api_token}", "Content-Type": "application/json"}
    print(f"☁️ Updating {label} ...")
    resp = requests.patch(url, headers=headers, json=data)
    print(f" Cloudflare {label}: {resp.status_code}")
    if not resp.ok:
        print(resp.text)
    return resp.ok


def main(request):
    try:
        print("=== SYNC-GCP-TO-CLOUDFLARE START ===")

        ips = get_external_ips()
        cf_token_secret = os.environ["CF_SECRET_NAME"]
        cf_api_token = get_secret(cf_token_secret)

        # Automatically detect configured zones from environment
        suffixes = ["DE", "COM", "AT", "CH"]
        zones = []
        for s in suffixes:
            zid = os.environ.get(f"CF_ZONE_ID_{s}")
            ridset = os.environ.get(f"CF_RULESET_ID_{s}")
            rid = os.environ.get(f"CF_RULE_ID_{s}")
            if zid and ridset and rid:
                zones.append({
                    "label": f"jobvector.{s.lower()}",
                    "zone_id": zid,
                    "ruleset_id": ridset,
                    "rule_id": rid
                })

        print(f" Found {len(zones)} zones to update")

        results = []
        for z in zones:
            ok = update_zone(z["label"], z["zone_id"], z["ruleset_id"], z["rule_id"], cf_api_token, ips)
            results.append({z["label"]: ok})

        print("=== SYNC-GCP-TO-CLOUDFLARE END ===")
        return jsonify({"success": True, "zones": results})

    except Exception as e:
        print(f" Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
