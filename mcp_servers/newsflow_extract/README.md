# URL提取服务 (newsflow-extract)

## 服务概述

`newsflow-extract` 是一个MCP服务，用于从指定网站URL提取所有链接。该服务使用Selenium Chrome WebDriver访问网站，等待页面完全渲染后提取所有a标签链接，并自动将相对路径转换为绝对路径。

## 功能说明

### 核心功能
- 访问网站并获取完整HTML（支持CSR客户端渲染网站）
- 提取所有`<a>`标签的href属性
- 自动将相对路径转换为绝对路径
- 过滤无效链接（javascript:、mailto:、#等）

### 技术方案

#### 1. 浏览器自动化
使用 **Selenium Chrome WebDriver** 无头模式访问网站，确保能够获取JavaScript渲染后的完整HTML。

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--headless")  # 无头模式，不显示浏览器窗口
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(
    ChromeDriverManager().install(), 
    options=options
)
driver.get(url)
driver.implicitly_wait(5)  # 等待页面完全渲染
html = driver.page_source
driver.quit()
```

**优势**：
- **无头模式**：不打开浏览器窗口，后台运行，性能更好
- **自动管理ChromeDriver**：webdriver-manager自动下载和管理对应版本的ChromeDriver
- **支持CSR网站**：可以获取JavaScript动态加载的内容
- **等待机制**：确保页面完全加载后再提取

#### 2. HTML解析
使用 **BeautifulSoup4** 解析HTML并提取链接。

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, 'html.parser')
links = soup.find_all('a', href=True)
```

#### 3. URL标准化
使用 `urllib.parse.urljoin` 将相对路径转换为绝对路径。

```python
from urllib.parse import urljoin

absolute_url = urljoin(base_url, relative_url)
```

## MCP工具定义

### extract_links_from_url

**描述**：从指定URL提取所有链接

**输入参数**：
- `url` (string, 必需): 网站URL，如 "https://example.com"

**返回结果**：
```json
{
  "links": [
    "https://example.com/article1",
    "https://example.com/article2",
    ...
  ],
  "count": 链接数量
}
```

**实现要点**：
1. 使用Selenium Chrome WebDriver访问URL
2. 等待页面完全渲染（`driver.implicitly_wait(5)`）
3. 获取渲染后的HTML（`driver.page_source`）
4. 关闭浏览器（`driver.quit()`）
5. 使用BeautifulSoup解析HTML
6. 提取所有`<a>`标签的href属性
7. 使用`urllib.parse.urljoin`转为绝对路径
8. 过滤掉`javascript:`、`mailto:`、`#`等特殊链接
9. 去重链接列表

**错误处理**：
- 网站无法访问：返回错误信息
- 超时：记录日志并返回已提取的链接
- 解析失败：返回空列表

## 依赖要求

- Python 3.8+
- selenium >= 4.0.0
- beautifulsoup4 >= 4.12.0
- webdriver-manager >= 4.0.0（自动管理ChromeDriver）
- Google Chrome浏览器（系统需安装，但无需手动配置ChromeDriver）

## 注意事项

1. **浏览器环境**：
   - 确保系统已安装Chrome浏览器
   - ChromeDriver由webdriver-manager自动管理，首次运行时会自动下载
2. **无头模式**：
   - 使用headless模式，不会打开浏览器窗口
   - 节省资源，适合服务器环境运行
3. **等待时间**：默认隐式等待5秒，可根据网站加载速度调整
4. **资源消耗**：每个请求会启动一个无头浏览器实例，处理完成后需及时关闭（driver.quit()）
5. **CSR支持**：虽然支持CSR网站，但某些需要复杂交互才能加载的内容可能仍无法获取

## 文件结构

```
newsflow_extract/
├── server.py      # MCP服务器入口
├── __init__.py
├── extractor.py   # 链接提取逻辑
└── README.md      # 本说明文档
```

## 开发状态

- [x] 技术方案设计
- [ ] MCP服务器框架搭建
- [ ] Selenium集成
- [ ] 链接提取逻辑实现
- [ ] URL标准化实现
- [ ] 错误处理
- [ ] 单元测试
- [ ] Cursor集成测试

