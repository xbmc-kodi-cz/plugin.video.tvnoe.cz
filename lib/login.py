import urllib3
import urllib.parse
import re

def try_login(username: str, password: str, return_id: str = "3118761757"):
    login_url = "https://www.tvnoe.cz/klub"
    live_url = "https://www.tvnoe.cz/live?view=livestream"

    data = {
        "noeuser": username,
        "noepass": password,
        "return": return_id,
        "login": "1"
    }
    encoded_data = urllib.parse.urlencode(data)

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) "
                       "Gecko/20100101 Firefox/142.0"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "sk,cs;q=0.8,en-US;q=0.5,en;q=0.3",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.tvnoe.cz/klub"
    }

    http = urllib3.PoolManager()

    resp = http.request(
        "POST",
        login_url,
        body=encoded_data,
        headers=headers
    )
    html = resp.data.decode("utf-8", errors="ignore")

    if resp.status != 200:
        print("Chyba pri overení dát skontrolujte prístup k serveru!!!")
        return None

    if "odhlásit" in html.lower():
        return get_paywall_livestream(headers, http, live_url, resp)

    else:
        print("Prihlasovacie údaje nie su správne, skontrolujte si meno a heslo !!!")

    # ---- COOKIE HANDLING ----


def get_paywall_livestream(headers, http, live_url, resp):
    set_cookie = resp.headers.get("Set-Cookie")
    cookie_header = {}
    if set_cookie:
        session_cookie = set_cookie.split(";", 1)[0]
        cookie_header = {"Cookie": session_cookie}
    live_headers = headers.copy()
    live_headers.update(cookie_header)
    live_resp = http.request("GET", live_url, headers=live_headers)
    live_html = live_resp.data.decode("utf-8", errors="ignore")
    # Regex na timeshiftSrc
    match = re.search(r"timeshiftSrc:\s*'([^']+\.m3u8)'", live_html)
    if match:
        return match.group(1)
    else:
        print("M3U8 link sa nenašiel")
        return None