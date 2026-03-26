"""
Chrome WebDriver 公共启动参数。

--remote-allow-origins=* 可缓解新版 ChromeDriver 与 Chrome 通信时的 net::ERR_CONNECTION_CLOSED。
"""
from selenium.webdriver.chrome.options import Options


def build_chrome_options(*, headless: bool = True) -> Options:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-allow-origins=*")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return options
