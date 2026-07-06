# 登录与 easycheck 授权流程

> 基于 `cache/1` 抓包数据整理的精简流程，仅保留获得最终 URL 所需的关键请求。

---

## 阶段一：登录获取 Session Cookie

### ① 触发 OAuth 登录

**请求** `GET https://base.onewo.com/api/auth/jwt/zytlogin`

触发服务端 OAuth 授权码流程。

**响应** `302 Found`

```
Location: https://gw.4009515151.com/heimdall/api/lebang/oauth/app/authorize?scopes=r-staff&state=c77b8ae7...&redirect_uri=https%3A%2F%2Fbase.onewo.com%2Fapi%2Fauth%2Fjwt%2Fzyttoken&response_type=code&client_id=fdef40ed...&sign=n&relogin=y&is_sso=0
```

### ② 跟随 302 → OAuth 授权页

**请求** `GET https://gw.4009515151.com/heimdall/api/lebang/oauth/app/authorize?scopes=r-staff&state=...&redirect_uri=...&response_type=code&client_id=...`

**响应** `302 Found`

```
Location: https://gw.4009515151.com/heimdallr/zyt/weblogin?is_qr_auth=0&is_sso=0&oauth_code=null&scopes=r-staff&state=...
```

> 该 HTTP 302 的 `state` 参数需保留，后续 POST 登录时携带。

### ③ 账号密码登录

**请求** `POST https://gw.4009515151.com/heimdall/api/oauth/authorize`

```json
{
  "clientId": "<client_id>",
  "redirectUrl": "https://base.onewo.com/api/auth/jwt/zyttoken",
  "scopes": "r-staff",
  "state": "<state>",
  "oauthCode": "null",
  "mobile": "138xxxxxxxx",
  "password": "your_password"
}
```

**响应** 登录成功，返回 `auth_code`（包含在后续重定向 URL 中，以 JSON 体返回）。

### ④ 用 auth_code 换取票根 token（JWT）

**请求** `GET https://base.onewo.com/api/auth/jwt/zyttoken?code=<auth_code>&state=...`

`code` 参数是 JWT 格式的 `authorization_code`。

**响应** `302 Found`

```
Location: https://base.onewo.com/gateway-front/#/index?flag=true&ticket=sys%3Aweb%3Atoken<RS256_JWT>
```

此时 `requests.Session()` 已自动管理 **`X-heimdall` Cookie**，后续可使用此 Cookie 免登录。

---

## 阶段二：利用 Session Cookie 免登录跳转 easycheck

### ⑤ 访问 easycheck 入口

**请求** `GET https://rm.vankeservice.com/api/easycheck/web/index?wkwebview=true&rurl=/nightAnswer`

**响应** `302 Found`

```
Location: https://gw.4009515151.com/heimdall/api/lebang/oauth/app/authorize?client_id=e8a2f963...&auto_login=y&scopes=r-staff&redirect_uri=https%3A%2F%2Frm.vankeservice.com%2Fapi%2Feasycheck%2Fweb%2Foauth%3Frurl%3D%2FnightAnswer&response_type=code&state=1783364205613
```

### ⑥ 携带 Cookie 自动授权（关键）

**请求** `GET https://gw.4009515151.com/heimdall/api/lebang/oauth/app/authorize?client_id=...&auto_login=y&redirect_uri=...&response_type=code&state=...`

**Cookie** `X-heimdall=fNrMPi5PCr+uXo69mc/O2Q==`

`auto_login=y` 加上有效的 `X-heimdall` Cookie 实现免登录自动授权。

**响应** `302 Found`

```
Location: https://rm.vankeservice.com/api/easycheck/web/oauth?rurl=/nightAnswer&code=<auth_code>&state=...
```

### ⑦ 换取 easycheck 的 access_token（最终结果）

**请求** `GET https://rm.vankeservice.com/api/easycheck/web/oauth?rurl=/nightAnswer&code=<auth_code>&state=...`

**响应** `302 Found`

```
Set-Cookie: access_token_easycheck=<JWT>; Path=/
Set-Cookie: JSESSIONID=CE2171524AF0AF89F88294C1764FC348; Path=/; HttpOnly
Location: https://rm.vankeservice.com/easycheck/#/nightAnswer?accessToken=<JWT>
```

最终获得：
- **`access_token_easycheck` Cookie**（JWT, HS256 签名）
- **`JSESSIONID` Cookie**
- **Location URL**（携带 `accessToken` 查询参数，可直接跳转）

---

## 总结流程图

```
┌─ 阶段一：登录 ──────────────────────────────────────────────┐
│                                                              │
│  ① GET /api/auth/jwt/zytlogin                               │
│      ↓ 302 (OAuth authorize)                                 │
│  ② GET /heimdall/api/lebang/oauth/app/authorize             │
│      ↓ 302 (login page)                                      │
│  ③ POST /heimdall/api/oauth/authorize                       │
│      (mobile + password) → 获得 auth_code                    │
│      ↓                                                       │
│  ④ GET /api/auth/jwt/zyttoken?code=<auth_code>              │
│      ↓ 302 → ticket=sys:web:token<JWT>                      │
│      → Session Cookie (X-heimdall) 已建立                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌─ 阶段二：免登录跳转 easycheck ───────────────────────────────┐
│                                                              │
│  ⑤ GET /api/easycheck/web/index?rurl=/nightAnswer           │
│      ↓ 302 (OAuth with auto_login=y)                         │
│  ⑥ GET /heimdall/api/lebang/oauth/app/authorize             │
│      (Cookie: X-heimdall=... & auto_login=y)                  │
│      ↓ 302 → 自动授权回调                                    │
│  ⑦ GET /api/easycheck/web/oauth?rurl=/nightAnswer&code=...   │
│      ↓ 302 → 最终结果                                        │
│      Set-Cookie: access_token_easycheck=<JWT>                │
│      Set-Cookie: JSESSIONID=...                              │
│      Location: .../nightAnswer?accessToken=<JWT>             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 实现要点

- 使用 `requests.Session()` 自动管理 Cookie、跟踪 302 重定向。
- 阶段一的步骤 ③ 可以复用任意账号的 mobile/password。
- 阶段二的 `auto_login=y` 结合 `X-heimdall` Cookie 可实现免密跳转。
- 最终 `access_token_easycheck` 即之前提到的 `ACCESS_TOKEN`（JWT payload 中 `sub: ACCESS_TOKEN`），可直接用于 easycheck 的 API 鉴权。
