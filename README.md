# get-easycheck-url

自动完成 OAuth 登录并获取 **easycheck** 授权访问链接（含 JWT accessToken）的命令行工具。

## 使用场景

需要访问 easycheck 系统时，手动登录流程繁琐。本工具自动完成整个 OAuth 授权流程，一步输出可直接在浏览器中打开的最终 URL。

## 快速使用

```bash
# 安装
pip install get-easycheck-url

# 运行
get-easycheck-url
```

按提示输入手机号和密码，即可获得最终访问 URL。

## 功能

- 自动完成 OAuth 登录（手机号 + 密码）
- 自动管理 Session Cookie（`X-heimdall` 等）
- 自动携带 `auto_login=y` 实现免密跳转
- 输出可直接访问的 easycheck URL（含 `accessToken`）

## 安装

### 从 PyPI

```bash
pip install get-easycheck-url
```

### 从源码

```bash
git clone https://github.com/Ntzy123/get-easycheck-url.git
cd get-easycheck-url
make setup      # 创建 venv 并安装依赖
```

或手动：

```bash
python -m venv .venv
.venv\Scripts\pip   install -e .   # Windows
source .venv/bin/pip install -e .  # Linux/macOS
```

## 使用

```bash
# 方式一：直接运行已安装的命令
get-easycheck-url

# 方式二：通过 Python 模块
python -m get_easycheck_url
```

程序会交互式地要求输入手机号和密码：

```
==================================================
  easycheck 授权链接获取工具
==================================================
请输入手机号: 138xxxxxxxx
请输入密码:

正在登录并获取 easycheck 链接，请稍候...

✅ easycheck 访问 URL:
https://rm.vankeservice.com/easycheck/#/nightAnswer?accessToken=eyJhbG...
```

## 作为库使用

```python
from get_easycheck_url import get_easycheck_url

url = get_easycheck_url("138xxxxxxxx", "your_password")
print(url)
# https://rm.vankeservice.com/easycheck/#/nightAnswer?accessToken=<JWT>
```

## 开发

### 环境要求

- Python >= 3.9
- requests >= 2.31.0

### 常用命令

| 命令                | 说明                     |
| ------------------- | ------------------------ |
| `make setup`        | 创建 venv 并安装依赖     |
| `make run`          | 运行应用                 |
| `make test`         | 运行测试（带覆盖率）     |
| `make build`        | 使用 PyInstaller 打包    |
| `make mirror`       | 切换 pip 到清华镜像源    |

### 测试

```bash
make test
```

### 打包

```bash
make build
```

输出为 `dist/get_easycheck_url_<时间戳>.exe`（单文件，无需 Python 环境）。

## 登录流程

工具内部依次执行以下步骤完成授权：

1. **触发 OAuth** — 请求 `zytlogin` 获取 authorize URL
2. **建立 Session** — 跟随 302 到 OAuth 授权页
3. **账号登录** — POST 手机号 + 密码，获取 `auth_code`
4. **换取 Ticket** — 用 `auth_code` 换取 JWT（session 获得 `X-heimdall` Cookie）
5. **访问 easycheck** — 请求 easycheck 入口，获取 `auto_login=y` 授权 URL
6. **自动授权** — 携带已有 Cookie 完成授权跳转
7. **获取结果** — 拿到最终 Location URL（含 `accessToken`）

详细流程见 [docs/login-flow.md](docs/login-flow.md)。

## API 参考

详见 [docs/get-easycheck-url-api.md](docs/get-easycheck-url-api.md)。

## 许可证

[MIT](LICENSE)
