import json
from pathlib import Path

cookie_str = "sid_guard=9ec7fd803c80b7128a50bc4547e32a43%7C1776347953%7C5184000%7CMon%2C+15-Jun-2026+13%3A59%3A13+GMT; sessionid=9ec7fd803c80b7128a50bc4547e32a43; sessionid_ss=9ec7fd803c80b7128a50bc4547e32a43; uid_tt=6e53b5b2e0d0d21c7e4bf4fbfbcfdd6c; ttwid=1%7CBjmkukIlKEIMnAKzIRsLu7IA2so-dIy7XtdTxSqlRws%7C1776355590%7C525512d4e81b8d7a8ed5e92ab240f5905b32dd0f48176947268daadef1ba8450; odin_tt=ab8921b64b5e73ae8aaa8fb5e9895bffa1b8f385b9480c1aa253ec9fb9ab174acd6b0ea52b2f9d5da562d6416a921a99c00a21d35047129431c04cf57abcd79d; n_mh=-Ir_u0umsPi7PInfv-xftlJgeFRPNiM2RFtqyKxxbm8; passport_csrf_token=018f8d5a3c9ad64329d021fad56977f1; d_ticket=abe9ca591b155032c54de1b65d4dcb4a29c11; my_rd=2; home_can_add_dy_2_desktop=1; passport_auth_status=18de5770bd2766bfbb22ee344b920674%2C; passport_auth_status_ss=18de5770bd2766bfbb22ee344b920674%2C; has_biz_token=false; webcast_local_quality=heiq; ssid_ucp_v1=1.0.0-KDdhNjM4OGMxMjRiMzIyNWU2MDJjZDI2ODQwNWMxNDJmMGUwYWRjMWIKIQids5C-6PWOARCx1oPPBhjvMSAMMLX6oe8FOAVA-wdIBBoCaGwiIDllYzdmZDgwM2M4MGI3MTI4YTUwYmM0NTQ3ZTMyYTQz; ssid_ucp_v1=1.0.0-KDdhNjM4OGMxMjRiMzIyNWU2MDJjZDI2ODQwNWMxNDJmMGUwYWRjMWIKIQids5C-6PWOARCx1oPPBhjvMSAMMLX6oe8FOAVA-wdIBBoCaGwiIDllYzdmZDgwM2M4MGI3MTI4YTUwYmM0NTQ3ZTMyYTQz; biz_trace_id=6c808abd; IsDouyinActive=true; passport_assist_user=CkC82TvOPGH3mQx2yGQn9JMfNvZVmWMca9Txn-mfQX76cgcblAW9l-fytX9-inrxyig9Gvah2vXi2ucte448oaz9GkoKPAAAAAAAAAAAAABQT7giL1vk09vY7PJwcOUXT5O-zLbNA3YyTiItwzIUdsLtOFMEgQJAHr-WtZGONwN0nhD8_o4OGImv1lQgASIBA7nQXwY%3D"

cookies = []
for part in cookie_str.split("; "):
    if "=" in part:
        name, _, value = part.partition("=")
        cookies.append({
            "name": name.strip(),
            "value": value.strip(),
            "domain": ".douyin.com",
            "path": "/",
            "secure": False,
            "httpOnly": False,
        })

cookie_header = "; ".join(c["name"] + "=" + c["value"] for c in cookies)

result = {
    "platform": "douyin",
    "name": "抖音",
    "extracted_at": "2026-04-17",
    "cookie_count": len(cookies),
    "cookies": cookies,
    "cookie_header": cookie_header,
}

out = Path(r"D:\Tools\creator-monitor\data\douyin_cookies.json")
out.parent.mkdir(parents=True, exist_ok=True)
content = json.dumps(result, ensure_ascii=False, indent=2)
out.write_text(content, encoding="utf-8")

print("Saved " + str(len(cookies)) + " cookies to " + str(out))
print("Header length: " + str(len(cookie_header)))
