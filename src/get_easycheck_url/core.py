"""easycheck 登录授权核心逻辑。

提供 get_easycheck_url(mobile, password) 函数，
自动完成 OAuth 登录 + Cookie 管理 + 免登跳转，
最终返回 easycheck 的可访问 URL。
"""

import urllib.parse
import requests

_RURL = "/nightAnswer"


def _parse_param(url: str, key: str) -> str:
    """从 URL 中提取指定参数的值（兼容参数位于 fragment 的情况）。"""
    parsed = urllib.parse.urlparse(url)
    # 形如 .../#/nightAnswer?accessToken=xxx 时参数在 fragment 里
    query = parsed.query or parsed.fragment.partition("?")[2]
    params = urllib.parse.parse_qs(query, keep_blank_values=True)
    return params[key][0]


def get_easycheck_url(mobile: str, password: str) -> str:
    """完成登录 + easycheck 授权，返回最终访问 URL。

    Args:
        mobile: 手机号。
        password: 密码。

    Returns:
        最终可访问的 Location URL（含 accessToken 参数）。

    Raises:
        RuntimeError: 任意 HTTP 或解析异常。
    """
    return _get_final_url(mobile, password)


def get_access_token(mobile: str, password: str) -> str:
    """完成登录 + easycheck 授权，仅返回 accessToken 值。

    Raises:
        RuntimeError: 任意 HTTP 或解析异常。
    """
    return _parse_param(_get_final_url(mobile, password), "accessToken")


def _get_final_url(mobile: str, password: str) -> str:
    """走完整授权流程，返回最终 Location URL。"""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/149.0.0.0 Safari/537.36"
            ),
        }
    )

    # ====== 阶段一：登录 ======

    # ① 触发 OAuth 登录
    resp = session.get(
        "https://base.onewo.com/api/auth/jwt/zytlogin",
        allow_redirects=False,
    )
    resp.raise_for_status()
    authorize_url = resp.headers["Location"]

    # 从 authorize_url 中提取 OAuth 参数（后续步骤需要）
    client_id = _parse_param(authorize_url, "client_id")
    redirect_uri = _parse_param(authorize_url, "redirect_uri")
    scopes = _parse_param(authorize_url, "scopes")
    state = _parse_param(authorize_url, "state")

    # ② 跟随 302 → OAuth 授权页（建立 session state）
    resp = session.get(authorize_url, allow_redirects=False)
    resp.raise_for_status()
    # login_url = resp.headers["Location"]  # 登录页 HTML，不需要跟随

    # ③ 账号密码 POST 登录
    resp = session.post(
        "https://gw.4009515151.com/heimdall/api/oauth/authorize",
        json={
            "clientId": client_id,
            "redirectUrl": redirect_uri,
            "scopes": scopes,
            "state": state,
            "oauthCode": "null",
            "mobile": mobile,
            "password": password,
        },
        allow_redirects=False,
    )
    resp.raise_for_status()

    # 解析 auth_code（可能 JSON 返回或 302 跳转）
    if resp.is_redirect:
        auth_code = _parse_param(resp.headers["Location"], "code")
    else:
        data = resp.json()
        auth_code = (
            data.get("code")
            or data.get("data", {}).get("code")
            or data.get("authorizationCode")
        )
    if not auth_code:
        raise RuntimeError(f"登录响应中未找到 auth_code: {resp.text[:300]}")

    # ④ 用 auth_code 换取票根 token（JWT）
    # 此时 session 自动获得 X-heimdall Cookie
    resp = session.get(
        f"{redirect_uri}?code={auth_code}&state={state}",
        allow_redirects=False,
    )
    resp.raise_for_status()
    # Location 中包含 ticket=sys:web:token<JWT>，仅确认登录成功

    # ====== 阶段二：免登录跳转 easycheck ======

    # ⑤ 访问 easycheck 入口
    resp = session.get(
        "https://rm.vankeservice.com/api/easycheck/web/index",
        params={"wkwebview": "true", "rurl": _RURL},
        allow_redirects=False,
    )
    resp.raise_for_status()
    easycheck_auth_url = resp.headers["Location"]

    # ⑥ 携带 X-heimdall Cookie + auto_login=y 自动授权
    resp = session.get(easycheck_auth_url, allow_redirects=False)
    resp.raise_for_status()
    oauth_callback_url = resp.headers["Location"]

    # ⑦ 获取最终结果（含 access_token_easycheck Cookie + Location URL）
    resp = session.get(oauth_callback_url, allow_redirects=False)
    resp.raise_for_status()

    final_url = resp.headers["Location"]
    return final_url
