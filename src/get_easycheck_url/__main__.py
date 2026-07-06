"""get-easycheck-url CLI 入口。

从用户输入获取手机号和密码，调用 core.get_easycheck_url()
并打印最终访问 URL。
"""

import sys
from get_easycheck_url.core import get_easycheck_url


def main():
    print("=" * 50)
    print("  easycheck 授权链接获取工具")
    print("=" * 50)

    mobile = input("请输入手机号: ").strip()
    password = input("请输入密码: ").strip()

    if not mobile or not password:
        print("错误：手机号和密码不能为空", file=sys.stderr)
        sys.exit(1)

    print("\n正在登录并获取 easycheck 链接，请稍候...")
    try:
        url = get_easycheck_url(mobile, password)
        print(f"\n✅ easycheck 访问 URL:\n{url}")
    except Exception as e:
        print(f"\n❌ 获取失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
