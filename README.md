# 🐟 EdgeDomain - 基于 Edge 浏览器的智能子域收集工具

<img width="2161" height="1410" alt="image" src="https://github.com/user-attachments/assets/c8f60f81-b5f8-4ddd-b016-9bfa35b09c57" />


## 📖 项目介绍

EdgeDomain 是一款基于 Edge 浏览器和 Selenium 开发的智能子域收集工具，专为网络安全从业者和渗透测试人员设计。通过模拟人工浏览行为，自动从 Bing 搜索引擎爬取指定主域名的相关子域，帮助安全人员快速构建目标网络资产图谱。

<img width="2245" height="1259" alt="image" src="https://github.com/user-attachments/assets/b59b4632-a6a7-425a-addc-63459ad3e42d" />


工具特点：

- 🤖 智能模拟人类浏览行为，降低被反爬检测的概率
- 🔄 自动翻页与内容加载，最多支持 999 页深度爬取
- 🧠 智能识别验证码等待时间，提高爬取成功率
- 📊 详细的爬取统计与结果导出功能
- 📧 支持爬取完成后自动发送邮件报告

## 🚀 功能亮点

| 功能           | 说明                                                         |
| -------------- | ------------------------------------------------------------ |
| 🔍 深度子域挖掘 | 通过 Bing 搜索引擎的 `site:` 语法，深度挖掘目标主域的所有相关子域 |
| 🛡️ 反反爬机制   | 集成多种反检测技术，包括浏览器特征伪装、随机延迟、滚动加载等 |
| 🔄 智能翻页     | 自动识别多种形态的 "下一页" 按钮，支持动态页面结构           |
| 📄 结果持久化   | 自动将爬取结果保存到本地文件，支持批量域名处理               |
| 📧 邮件通知     | 爬取完成后自动发送详细报告到指定邮箱，包含统计信息和子域列表 |
| ⚙️ 高度可配置   | 支持代理设置、爬取深度调整等多种自定义配置                   |

## 📋 安装指南

### 前置条件

- Python 3.8 及以上版本
- Microsoft Edge 浏览器
- 对应版本的 [EdgeDriver](https://developer.microsoft.com/zh-cn/microsoft-edge/tools/webdriver/)（需放置在脚本同一目录）

### 快速安装

1. 克隆本项目

```bash
git clone https://github.com/Bifishone/EdgeDomain.git
cd EdgeDomain
```



1. 安装依赖包

```bash
pip install -r requirements.txt
```



> 依赖说明：`selenium`, `tldextract`, `colorama`, `python-dotenv`

## 💻 使用方法

### 基本用法

1. 准备域名列表文件（默认为 `domain.txt`），每行一个主域名

```txt
example.com
test.com
```



1. 运行工具

```bash
python EdgeDomain.py
```

### 高级参数

| 参数          | 说明             | 示例                                          |
| ------------- | ---------------- | --------------------------------------------- |
| `-f`/`--file` | 指定域名列表文件 | `python EdgeDomain.py -f my_domains.txt`      |
| `--proxy`     | 设置代理服务器   | `python EdgeDomain.py --proxy 127.0.0.1:7890` |

### 配置调整

可在代码中调整核心配置参数以优化爬取效果：

```python
MAX_PAGES = 999  # 最大爬取页数
SCROLL_PAUSE = 2  # 滚动等待时间
RETRY_LIMIT = 15  # 元素重试次数
VERIFICATION_TIME = 1  # 验证码处理时间（秒）
```

## 📊 结果展示

爬取完成后，结果将保存在 `results` 目录下，每个主域名对应一个结果文件：



```plaintext
results/
├── Edge_results_example.com.txt
└── Edge_results_test.com.txt
```



同时会自动发送包含以下信息的邮件报告：

- 总爬取域名数量
- 总获取子域名数量
- 各域名的详细爬取统计
- 前 20 个子域名预览

## 🔍 工作原理

1. 使用 Selenium 控制 Edge 浏览器访问 Bing 搜索引擎
2. 对每个主域名执行 `site:domain` 搜索
3. 自动滚动页面加载所有结果内容
4. 从搜索结果中提取并解析所有相关子域
5. 智能识别并点击 "下一页" 按钮，重复爬取过程
6. 爬取完成后生成结果文件并发送邮件报告

## 🛠️ 常见问题

### Q: 提示找不到 EdgeDriver 怎么办？

A: 请确保 `msedgedriver.exe` 与脚本在同一目录，且版本与你的 Edge 浏览器匹配。

### Q: 爬取过程中遇到验证码怎么办？

A: 工具会自动等待一段时间（可通过 `VERIFICATION_TIME` 配置），你可以在这段时间手动完成验证码验证。

### Q: 邮件发送失败如何解决？

A: 检查邮箱配置（账号、授权码）和网络连接，确保 SMTP 服务已开启。

## 📜 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

## 👤 关于作者

一只鱼（Bifishone）

- 网络安全爱好者
- 专注于信息收集与渗透测试自动化工具开发
- 欢迎交流与合作！

------



✨ 感谢使用 EdgeDomain！如果觉得本工具对你有帮助，欢迎点亮 Star 支持一下～ ✨
