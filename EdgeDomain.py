import os
import time
import random
import tldextract
import argparse
import hashlib
from colorama import init, Fore, Style
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    InvalidSelectorException
)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr

init(autoreset=True)

# ======================  核心配置（优化后）  ======================
MAX_PAGES = 999  # 最大爬取页数（保持不变）
SCROLL_PAUSE = 2  # 滚动等待时间（延长，确保内容加载）
RETRY_LIMIT = 15  # 元素重试次数
VERIFICATION_TIME = 1  # 验证码处理时间（秒）
CONSECUTIVE_SAME_LIMIT = 150  # 连续相同页面阈值（放宽）
CONTENT_TIMEOUT = 20  # 内容加载超时时间（延长至40秒）
NEXT_PAGE_RETRY = 3  # 下一页按钮查找重试次数
# ================================================================


def print_banner():
    """打印程序的横幅信息"""
    banner = r"""
                    /|\
                  /  |  \
                '/ ` |   '\
                |    |    |
                |    |    |
                |    |    |
                |    |    |
                |    |    |
                |    |    |
                |    |    |
                |    |    |
                |    |    |
                |'.·´|`·.'|
                |;::;|;::;|
                |;::;|;::;|
                |;::;|;::;|
                |;::;|;::;|
                |.·´¯`·.|
                |;      ';|
                |`·._.·´|
                |;::;|;::;|
 |¯`·._.·´¯¯¯¯¯¯¯¯¯`·._.·´¯|
 |              Bifish                '|
 |.·´¯`·.__________ '.·´¯`·.|
 |.·´¯`·.___         '___.·´¯`·.|
               .·´      `·.
               |.·´¯`·..·´|
               |`·._.·´`·.|
               |.·´¯`·..·´|
               |`·._.·´`·.|
               |.·´¯`·..·´|
               `·.      .·´
            . · ´¯¯¯¯` · .
          ,' ,'  .·´¯`·.   ', ',
          ', ',  `·._.·´  ,' ,'
            '  ,_____,  '
                 `·..·´
    """
    print(Fore.CYAN + banner)
    print(Fore.GREEN + "=" * 60)
    print(Fore.YELLOW + "  EdgeDomain - 基于Edge浏览器的域名收集器（v1.3版） 辉小鱼")
    print(Fore.GREEN + "=" * 60)
    print(Style.RESET_ALL)


def setup_driver(proxy=None):
    """设置并返回 Edge 浏览器驱动（保持不变）"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        driver_path = os.path.join(current_dir, "msedgedriver.exe")
        if not os.path.exists(driver_path):
            print(Fore.RED + f"[-] 未找到 Edge 驱动: {driver_path}")
            print(Fore.YELLOW + "[!] 请确保 msedgedriver.exe 在脚本同一目录下")
            return None
        try:
            from selenium.webdriver.edge.options import Options
            options = Options()
        except ImportError:
            options = webdriver.EdgeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        )
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        service = webdriver.edge.service.Service(driver_path)
        driver = webdriver.Edge(service=service, options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
            """
        })
        return driver
    except Exception as e:
        print(Fore.RED + f"[-] 驱动设置失败: {e}")
        return None


def auto_scroll(driver):
    """自动滚动页面（延长等待，确保内容加载）"""
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0  # 最多滚动5次（避免无限循环）
        while scroll_attempts < 5:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE)  # 延长滚动间隔
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1
        time.sleep(2)  # 额外等待2秒确保内容加载
    except Exception as e:
        print(Fore.RED + f"[-] 自动滚动失败: {e}")


def get_page_content_hash(driver):
    """优化内容哈希计算（兼容更多结果容器）"""
    try:
        # 扩展结果区域选择器（覆盖更多页面结构）
        content_selectors = [
            'li.b_algo', 'div.b_algo',  # 主流结果容器
            'div.b_ans', 'div.b_results > div',  # 补充结果容器
            'ul.sb_results > li'  # 旧版结果列表
        ]
        content_text = ""
        for selector in content_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                content_text += " ".join([el.text for el in elements])
        # 若仍无内容，尝试获取页码文本辅助判断
        if not content_text:
            page_info = driver.find_elements(By.CSS_SELECTOR, 'span.sb_pagS')  # 页码提示
            content_text = " ".join([el.text for el in page_info])
        return hashlib.md5(content_text.encode('utf-8')).hexdigest()
    except Exception as e:
        print(Fore.RED + f"[-] 获取页面内容哈希失败: {e}")
        return hashlib.md5(driver.page_source.encode('utf-8')).hexdigest()


def find_next_page(driver):
    """增强下一页按钮识别（增加选择器+重试机制）"""
    # 扩展选择器（覆盖更多形态的下一页按钮）
    selectors = [
        'a[title="Next page"]', 'a[aria-label="Next page"]', 'a.sb_pagN',
        'a[class*="sb_pagN"]',  # 含动态class的按钮
        'a[href*="first="][href*="FORM=PERE"]'  # 带分页参数的链接
    ]
    xpath_selectors = [
        '//a[contains(text(), "下一页")]', '//a[contains(text(), "Next")]',
        '//a[contains(text(), "»")]',  # 带右箭头的按钮
        '//a[parent::li[class="sb_pagN"]]',  # 父元素为分页容器的按钮
        '//a[contains(@href, "page=") and contains(text(), "下")]'  # 带页码参数的中文按钮
    ]

    # 重试机制：最多重试3次（每次重试前滚动页面）
    for attempt in range(NEXT_PAGE_RETRY):
        # 尝试CSS选择器
        for selector in selectors:
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, selector)
                if btns and btns[0].is_displayed():  # 确保按钮可见
                    return btns[0]
            except InvalidSelectorException:
                continue
        # 尝试XPath选择器
        for xpath in xpath_selectors:
            try:
                btns = driver.find_elements(By.XPATH, xpath)
                if btns and btns[0].is_displayed():
                    return btns[0]
            except Exception as e:
                continue
        # 重试前等待并滚动
        if attempt < NEXT_PAGE_RETRY - 1:
            print(Fore.YELLOW + f"[!] 第{attempt + 1}次未找到下一页按钮，重试中...")
            auto_scroll(driver)  # 重新滚动页面
            time.sleep(2)  # 等待2秒
    return None


def crawl_domain(driver, query, proxy=None):
    """优化爬取逻辑（增强翻页稳定性）"""
    base_domain = query.split(':')[1]
    all_subdomains = set()
    page_num = 1
    consecutive_same_count = 0
    driver.get(f"https://www.bing.com/search?q={query}")
    print(Fore.YELLOW + f"[+] 手动处理验证码（若有），{VERIFICATION_TIME} 秒后继续...")
    time.sleep(VERIFICATION_TIME)
    prev_content_hash = get_page_content_hash(driver)

    while page_num <= MAX_PAGES:
        print(Fore.YELLOW + f"\n[+] 第 {page_num} 页 | 开始爬取")
        auto_scroll(driver)  # 确保内容加载完全

        # 提取子域
        current_subdomains = extract_subdomains(driver, base_domain)
        new_subdomains = current_subdomains - all_subdomains
        all_subdomains.update(new_subdomains)
        print(Fore.GREEN + f"[+] 第 {page_num} 页 | 新增 {len(new_subdomains)} 个 | 累计 {len(all_subdomains)}")
        if new_subdomains:
            for idx, subdomain in enumerate(new_subdomains, 1):
                print(Fore.CYAN + f"    {idx}. {subdomain}")

        # 查找下一页按钮（带重试）
        next_btn = find_next_page(driver)
        if not next_btn:
            # 最后尝试一次强制滚动到底部再查找
            print(Fore.YELLOW + "[!] 最后尝试查找下一页按钮...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            next_btn = find_next_page(driver)
            if not next_btn:
                print(Fore.RED + "[-] 确认未找到下一页按钮，终止爬取")
                break

        # 点击下一页并验证
        try:
            current_url = driver.current_url
            current_content_hash = get_page_content_hash(driver)
            # 确保按钮在可视区域
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            time.sleep(1)  # 等待按钮可点击
            next_btn.click()

            # 等待页面加载（延长超时+双重验证）
            WebDriverWait(driver, CONTENT_TIMEOUT).until(
                lambda d: d.current_url != current_url or
                          get_page_content_hash(d) != current_content_hash
            )

            # 验证页面变化
            new_url = driver.current_url
            new_content_hash = get_page_content_hash(driver)
            if new_url == current_url and new_content_hash == current_content_hash:
                consecutive_same_count += 1
                print(Fore.RED + f"[!] 页面未刷新！连续 {consecutive_same_count} 次")
            else:
                consecutive_same_count = 0  # 重置计数器
                prev_content_hash = new_content_hash

            # 检查连续相同页面阈值
            if consecutive_same_count >= CONSECUTIVE_SAME_LIMIT:
                print(Fore.RED + f"[!] 连续 {CONSECUTIVE_SAME_LIMIT} 次页面未刷新，终止爬取")
                break

            page_num += 1
            time.sleep(random.uniform(3, 6))  # 延长随机延迟，降低反爬风险
        except TimeoutException:
            print(Fore.YELLOW + "[!] 页面加载超时，重试当前页...")
            # 超时后重试当前页（最多2次）
            driver.get(current_url)  # 重新加载当前页
            time.sleep(5)
            continue
        except Exception as e:
            print(Fore.RED + f"[-] 翻页错误: {e}，重试中...")
            time.sleep(5)
            continue

    return all_subdomains, page_num - 1


def extract_subdomains(driver, base_domain):
    """提取子域（保持不变）"""
    subdomains = set()
    selectors = ['li.b_algo a', 'div.b_ans a', 'footer a', 'aside a', 'div.b_algo a']
    for selector in selectors:
        try:
            for a in driver.find_elements(By.CSS_SELECTOR, selector):
                try:
                    link = a.get_attribute('href')
                    if not link:
                        continue
                    extracted = tldextract.extract(link)
                    full_domain = f"{extracted.subdomain}.{extracted.domain}.{extracted.suffix}".lstrip('.')
                    if base_domain in full_domain and full_domain != base_domain:
                        subdomains.add(full_domain)
                except Exception as e:
                    print(Fore.RED + f"[-] 提取子域失败: {e}")
        except Exception as e:
            print(Fore.RED + f"[-] 查找元素失败: {e}")
    return subdomains


def generate_email_content(domain_results, total_domains, total_subdomains, execution_time):
    """生成详细的邮件内容，包含爬取的具体子域列表"""
    content = f"""
📊 EdgeDomain 子域爬取完成报告 📊

尊敬的辉小鱼先生：

EdgeDomain 爬虫已完成所有域名的子域爬取工作！以下是详细报告：

📋 总体统计：
  • 处理主域名总数：{total_domains} 个
  • 总获取子域名：{total_subdomains} 个
  • 执行时间：{execution_time:.2f} 秒

🔍 各域名详细结果：
"""

    for domain, (subdomains, pages, time_taken) in domain_results.items():
        content += f"""
  • {domain}:
    - 爬取页数：{pages}
    - 获取子域名数量：{len(subdomains)}
    - 耗时：{time_taken:.2f} 秒
    - 前20个子域名（完整列表见附件）：
"""
        # 添加前20个子域名
        subdomain_list = list(subdomains)
        for i, subdomain in enumerate(subdomain_list[:20], 1):
            content += f"      {i}. {subdomain}\n"
        if len(subdomains) > 20:
            content += f"      ... 等 {len(subdomains)} 个子域名\n"

    content += """

💡 说明：
- 所有结果已保存到本地 results 目录
- 每个主域名对应一个结果文件

🚀 祝您渗透测试顺利，必出高危漏洞！

EdgeDomain 爬虫助手 🤖
"""
    return content


def send_email(sender_email, sender_password, receiver_email, subject, content):
    """发送邮件（简化版，只尝试一次）"""
    try:
        print(Fore.YELLOW + "[+] 准备发送邮件...")

        # 创建邮件对象
        message = MIMEMultipart()
        message['From'] = formataddr((str(Header("EdgeDomain 爬虫助手", 'utf-8')), sender_email))
        message['To'] = receiver_email
        message['Subject'] = Header(subject, 'utf-8')

        # 添加邮件正文
        message.attach(MIMEText(content, 'plain', 'utf-8'))

        # 尝试 SSL 连接
        print(Fore.YELLOW + "[+] 连接 SMTP 服务器...")
        with smtplib.SMTP_SSL('smtp.qq.com', 465) as server:
            server.set_debuglevel(0)  # 设置为 1 可查看详细调试信息
            print(Fore.YELLOW + "[+] 正在进行身份验证...")
            server.login(sender_email, sender_password)
            print(Fore.YELLOW + "[+] 身份验证成功，正在发送邮件...")
            server.sendmail(sender_email, [receiver_email], message.as_string())
            print(Fore.GREEN + "[✓] 邮件发送成功！")
            return True

    except smtplib.SMTPException as e:
        if "b'\\x00\\x00\\x00'" in str(e):
            print(Fore.YELLOW + "[!] 出现 SMTP 通信特殊异常，但邮件可能已发送成功")
            print(Fore.YELLOW + "[!] 请检查邮箱确认")
            return True
        else:
            print(Fore.RED + f"[-] SMTP 错误: {str(e)}")
            print(Fore.YELLOW + "[!] 请检查邮箱账号、授权码和网络连接")
    except Exception as e:
        print(Fore.RED + f"[-] 发送邮件时发生未知错误: {str(e)}")

    return False



if __name__ == "__main__":
    # 主程序逻辑与之前一致，确保结果保存和邮件发送正常
    print_banner()
    parser = argparse.ArgumentParser(description='Bing 子域爬取（优化版）')
    parser.add_argument('-f', '--file', type=str, default='domain.txt', help='域名列表文件，默认为 domain.txt')
    parser.add_argument('--proxy', type=str, default=None, help='代理，如 127.0.0.1:7890')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(Fore.RED + f"[-] 未找到文件: {args.file}")
        exit(1)
    with open(args.file, 'r', encoding='utf-8') as f:
        domains = f.read().splitlines()
    if not domains:
        print(Fore.RED + f"[-] 文件 {args.file} 为空")
        exit(1)

    driver = setup_driver(args.proxy)
    if not driver:
        exit(1)

    domain_results = {}
    total_subdomains = 0
    start_time = time.time()
    try:
        for domain in domains:
            query = f'site:{domain}'
            domain_start_time = time.time()
            subdomains, pages = crawl_domain(driver, query, args.proxy)
            if subdomains:
                os.makedirs('results', exist_ok=True)
                result_file = f'results/Edge_results_{domain}.txt'
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(subdomains))
                print(Fore.GREEN + f"[+] 结果已保存至: {result_file}")
            else:
                print(Fore.YELLOW + f"[-] 未爬取到 {domain} 的子域名，未生成文件")
            time_taken = time.time() - domain_start_time
            domain_results[domain] = (subdomains, pages, time_taken)
            total_subdomains += len(subdomains)
            print(Fore.GREEN + f"\n[+] 爬取 {domain} 完成 | 总子域: {len(subdomains)} | 耗时: {time_taken:.2f} 秒")
            delay = random.uniform(4, 8)
            print(Fore.YELLOW + f"[+] 准备爬取下一个域名，{delay:.1f} 秒后继续...")
            time.sleep(delay)
    except Exception as e:
        print(Fore.RED + f"[-] 爬取过程中发生错误: {e}")
    finally:
        if driver:
            print(Fore.YELLOW + "\n[+] 所有域名爬取完成，关闭浏览器...")
            driver.quit()

    execution_time = time.time() - start_time
    email_content = generate_email_content(domain_results, len(domains), total_subdomains, execution_time)
    config = {
        "sender_email": "1794686508@qq.com",
        "sender_password": "busnjcluyxtlejgc",
        "receiver_email": "shenghui3301@163.com",
        "subject": f"📧 EdgeDomain 爬取完成！共获取 {total_subdomains} 个子域名",
        "content": email_content
    }
    email_sent = send_email(** config)
    if email_sent:
        print(Fore.GREEN + "\n[✓] 爬取和通知流程全部完成！")
    else:
        print(Fore.RED + "\n[-] 爬取完成，但邮件通知失败")
        print(Fore.YELLOW + "[*] 请检查邮箱配置和网络连接")