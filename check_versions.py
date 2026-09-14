#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常用软件最新版离线安装包自动检测脚本
支持四种检测模式：
  increment - 从基础版本递增检测（默认）
  redirect  - 访问固定地址，从 302 Location 头提取版本号和完整下载链接
  fixed     - 固定下载地址，版本号手动维护，只检测文件可用性
  scrape    - 从官网页面抓取版本号，固定下载地址，计算MD5校验
"""

import hashlib
import json
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JSON = os.path.join(BASE_DIR, 'data.json')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# 产品配置
PRODUCTS = [
    {
        'name': 'LDPlayer 9',
        'name_cn': '雷电模拟器 9',
        'icon': '9',
        'icon_color': 'linear-gradient(135deg, #ff6b35, #f7931e)',
        'category': '模拟器',
        'detect_type': 'increment',
        'base_version': '9.5.37',
        'url_pattern': 'https://lddl01.ldmnq.com/download/leidian9/ldinst_{ver}.exe',
        'param_format': '?v={ts}&n=ldinst_{ver}_ld_{channel}_ld.exe',
        'channel': '407594',
        'official_site': 'https://www.ldmnq.com/',
    },
    {
        'name': 'LDPlayer 14',
        'name_cn': '雷电模拟器 14',
        'icon': '14',
        'icon_color': 'linear-gradient(135deg, #00d4ff, #7b2ff7)',
        'category': '模拟器',
        'detect_type': 'increment',
        'base_version': '14.0.27',
        'url_pattern': 'https://lddl01.ldmnq.com/download/leidian14/ldinst_{ver}.exe',
        'param_format': '?v={ts}&n=ldinst_{ver}_ld_{channel}_ld.exe',
        'channel': '412570',
        'official_site': 'https://www.ldmnq.com/',
    },
    {
        'name': 'Thunder',
        'name_cn': '迅雷',
        'icon': '迅',
        'icon_color': 'linear-gradient(135deg, #1e88e5, #00acc1)',
        'category': '下载工具',
        'detect_type': 'increment',
        'base_version': '25.1.13.1631',
        'url_pattern': 'https://down.sandai.net/thunder_pc/ThunderSetup{ver}up.exe',
        'param_format': '',
        'channel': '',
        'official_site': 'https://www.xunlei.com/',
    },
    {
        'name': 'WeChat',
        'name_cn': '微信',
        'icon': '微',
        'icon_color': 'linear-gradient(135deg, #07c160, #10ad56)',
        'category': '社交沟通',
        'detect_type': 'increment',
        'base_version': '4.1.13',
        'version_display': '4.1.13.65',
        'url_pattern': 'https://dldir1v6.qq.com/weixin/Universal/Windows/WeChatWin_{ver}.exe',
        'param_format': '',
        'channel': '',
        'official_site': 'https://pc.weixin.qq.com/',
    },
    {
        'name': 'Sogou Pinyin',
        'name_cn': '搜狗输入法',
        'icon': '搜',
        'icon_color': 'linear-gradient(135deg, #ff6b35, #ff8c42)',
        'category': '输入法',
        'detect_type': 'increment',
        'base_version': '16.8.0.4914',
        'url_pattern': 'https://ime.gtimg.com/pc/build/_sogou_pinyin_{ver}_0.exe',
        'param_format': '',
        'channel': '',
        'official_site': 'https://pinyin.sogou.com/windows/',
    },
    {
        'name': 'YY',
        'name_cn': '歪歪语音',
        'icon': 'Y',
        'icon_color': 'linear-gradient(135deg, #00d4ff, #0099cc)',
        'category': '社交沟通',
        'detect_type': 'increment',
        'base_version': '9.59.0.0',
        'url_pattern': 'https://dl-limit.yystatic.com/4/setup/YYSetup-{ver}-zh-CN.exe',
        'param_format': '',
        'channel': '',
        'official_site': 'https://www.yy.com/web/pcyy_download/',
    },
    {
        'name': 'QQMusic',
        'name_cn': 'QQ音乐',
        'icon': 'Q',
        'icon_color': 'linear-gradient(135deg, #31c27c, #1db954)',
        'category': '影音娱乐',
        'detect_type': 'scrape',
        'check_url': 'https://y.qq.com/download/download.html',
        'version_regex': r'最新版:(\d+\.\d+\.\d+)',
        'date_regex': r'发布时间[：:]\s*(\d{4}-\d{2}-\d{2})',
        'version': '22.6.1',
        'download_url': 'https://y.qq.com/download/download.html',
        'official_site': 'https://y.qq.com/download/download.html',
    },
    {
        'name': 'Xshell',
        'name_cn': 'Xshell',
        'icon': 'X',
        'icon_color': 'linear-gradient(135deg, #667eea, #764ba2)',
        'category': '开发工具',
        'detect_type': 'scrape',
        'check_url': 'https://www.xshell.com/zh/xshell-update-history/',
        'version_regex': r'Xshell\s*(\d+)\s*Build\s*(\d+)',
        'date_regex': r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        'version': '8.0.0110',
        'download_url': 'https://www.xshell.com/zh/xshell-update-history/',
        'official_site': 'https://www.xshell.com/zh/xshell-update-history/',
    },
    {
        'name': 'XMind',
        'name_cn': 'XMind',
        'icon': 'M',
        'icon_color': 'linear-gradient(135deg, #f7931e, #ff6b35)',
        'category': '办公效率',
        'detect_type': 'redirect',
        'check_url': 'https://xmind.cn/zen/download/win64/',
        'version_regex': r'Xmind-for-Windows-x64bit-(\d+\.\d+\.\d+)-',
        'official_site': 'https://xmind.cn/',
    },
    {
        'name': 'WinHex',
        'name_cn': 'WinHex',
        'icon': 'W',
        'icon_color': 'linear-gradient(135deg, #667eea, #764ba2)',
        'category': '开发工具',
        'detect_type': 'scrape',
        'check_url': 'https://www.x-ways.net/winhex/',
        'version_regex': r'WinHex\s*(\d+\.\d+(?:\s*SR-\d+)?)',
        'version': '21.8 SR-6',
        'download_url': 'https://www.x-ways.net/winhex.zip',
        'official_site': 'https://www.x-ways.net/winhex/',
    },
    {
        'name': 'XYplorer',
        'name_cn': 'XYplorer',
        'icon': 'X',
        'icon_color': 'linear-gradient(135deg, #00acc1, #1e88e5)',
        'category': '办公效率',
        'detect_type': 'scrape',
        'check_url': 'https://www.xyplorer.com/',
        'version_regex': r'version\s*\((\d+\.\d+\.\d+\.\d+)',
        'version': '28.30.2600',
        'download_url': 'https://www.xyplorer.com/download/xyplorer64_full_noinstall.zip',
        'official_site': 'https://www.xyplorer.com/',
    },
]

MAX_INCREMENT = 30  # 最多递增检测30个版本


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """禁止跟随重定向，302/301视为不存在（用于increment模式）"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class CaptureRedirect(urllib.request.HTTPRedirectHandler):
    """捕获重定向Location，不跟随（用于redirect模式）"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_no_redirect_opener = urllib.request.build_opener(NoRedirect)
_capture_redirect_opener = urllib.request.build_opener(CaptureRedirect)


def check_url(url):
    """检测URL是否存在，返回 (exists, size, last_modified)
    不跟随重定向：302/301（如CDN跳转404页）视为文件不存在
    """
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': UA})
        with _no_redirect_opener.open(req, timeout=10) as resp:
            size = resp.headers.get('Content-Length', '0')
            last_modified = resp.headers.get('Last-Modified', '')
            return resp.status == 200, int(size), last_modified
    except urllib.error.HTTPError:
        return False, 0, ''
    except Exception:
        return False, 0, ''


def check_url_follow(url):
    """检测URL（跟随重定向），返回 (exists, size, last_modified)
    用于fixed模式，因为有些固定地址会302到CDN
    """
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            size = resp.headers.get('Content-Length', '0')
            last_modified = resp.headers.get('Last-Modified', '')
            return resp.status == 200, int(size), last_modified
    except urllib.error.HTTPError as e:
        # 403 等也尝试获取信息
        size = e.headers.get('Content-Length', '0') if e.headers else '0'
        return False, int(size) if size.isdigit() else 0, ''
    except Exception:
        return False, 0, ''


def get_redirect_location(url):
    """获取302重定向的Location头，返回 (location, status)"""
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': UA})
        with _capture_redirect_opener.open(req, timeout=15) as resp:
            return resp.url if resp.status in (301, 302) else None, resp.status
    except urllib.error.HTTPError as e:
        location = e.headers.get('Location', '') if e.headers else ''
        return location, e.code
    except Exception:
        return None, 0


def increment_version(version):
    """递增版本号的最后一段，支持任意段数"""
    parts = version.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    return '.'.join(parts)


def detect_increment(product):
    """递增检测模式：从 base_version 开始递增检测"""
    current = product['base_version']
    latest = current
    latest_size = 0
    latest_date = ''

    # 先确认 base_version 存在
    url = product['url_pattern'].format(ver=current)
    exists, size, date = check_url(url)
    if exists:
        latest_size = size
        latest_date = date
    else:
        print(f"  ⚠️ 警告: 基础版本 {current} 不存在，可能已下架或网络异常")

    # 递增检测
    for _ in range(MAX_INCREMENT):
        next_ver = increment_version(current)
        url = product['url_pattern'].format(ver=next_ver)
        exists, size, date = check_url(url)
        if exists:
            latest = next_ver
            latest_size = size
            latest_date = date
            current = next_ver
            time.sleep(0.3)
        else:
            break

    # 生成下载链接
    full_url = product['url_pattern'].format(ver=latest)
    if product.get('param_format'):
        timestamp = int(time.time() * 1000)
        param_url = full_url + product['param_format'].format(
            ts=timestamp, ver=latest, channel=product.get('channel', '')
        )
    else:
        param_url = full_url

    return latest, full_url, param_url, latest_size, latest_date, ''


def detect_redirect(product):
    """重定向检测模式：访问固定地址，从302 Location提取版本号和完整链接"""
    location, status = get_redirect_location(product['check_url'])
    if not location:
        print(f"  ⚠️ 警告: 未获取到重定向地址 (status={status})")
        return product.get('version', '未知'), product['check_url'], product['check_url'], 0, ''

    # 从Location提取版本号
    version = '未知'
    regex = product.get('version_regex', r'(\d+\.\d+\.\d+)')
    m = re.search(regex, location)
    if m:
        version = m.group(1)

    # 获取文件大小和修改时间（跟随重定向）
    exists, size, date = check_url_follow(location)

    return version, location, location, size, date, ''


def detect_fixed(product):
    """固定地址模式：版本号手动维护，只检测文件可用性"""
    url = product['download_url']
    exists, size, date = check_url_follow(url)
    if not exists and size == 0:
        print(f"  ⚠️ 警告: 固定地址不可用，可能链接已失效")
    version = product.get('version', '最新版')
    return version, url, url, size, date, ''


def get_file_md5(url, max_retries=3):
    """下载文件并计算MD5，返回md5十六进制字符串。支持重试。"""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=180) as resp:
                md5 = hashlib.md5()
                total = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    md5.update(chunk)
                    total += len(chunk)
                if total > 0:
                    return md5.hexdigest()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  MD5下载重试 ({attempt+1}/{max_retries}): {e}")
                time.sleep(2)
            else:
                print(f"  ⚠️ MD5计算失败: {e}")
    return ''


def detect_scrape(product):
    """抓取模式：从官网页面抓取版本号和发布日期
    下载地址为网页时不计算MD5；为文件时计算MD5
    版本号优先使用配置默认值，官网抓取仅作参考
    """
    default_version = product.get('version', '未知')
    scraped_version = None
    scraped_date = None

    # 从官网抓取版本号和发布日期
    try:
        req = urllib.request.Request(product['check_url'], headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        # 抓取版本号（支持多捕获组，用.连接）
        regex = product.get('version_regex')
        if regex:
            m = re.search(regex, html, re.I)
            if m:
                groups = [g for g in m.groups() if g]
                if len(groups) > 1:
                    # Xshell 格式: 主版本.Build号 → 主版本.0.Build号
                    if 'Build' in regex or 'build' in regex:
                        scraped_version = f"{groups[0]}.0.{groups[1]}"
                    else:
                        scraped_version = '.'.join(groups)
                else:
                    scraped_version = groups[0]
                print(f"  官网版本: {scraped_version} (参考)")

        # 抓取发布日期
        date_regex = product.get('date_regex')
        if date_regex:
            m = re.search(date_regex, html, re.I)
            if m:
                scraped_date = m.group(1)
                # 统一日期格式为 YYYY-MM-DD
                scraped_date = scraped_date.replace('/', '-').replace('年', '-').replace('月', '-').replace('日', '')
                print(f"  发布日期: {scraped_date}")
    except Exception as e:
        print(f"  ⚠️ 官网抓取失败: {e}")

    # 版本号决策：优先使用配置的默认版本号
    if default_version and default_version != '未知':
        version = default_version
        if scraped_version and scraped_version not in default_version:
            print(f"  ⚠️ 官网版本({scraped_version})与配置版本({default_version})不一致，以配置为准")
    elif scraped_version:
        version = scraped_version
    else:
        version = default_version

    # 获取文件信息（仅当下载地址是文件时）
    url = product['download_url']
    is_webpage = url.endswith('.html') or url.endswith('/') or 'download.html' in url or 'update-history' in url
    size = 0
    date = ''
    md5 = ''

    if is_webpage:
        # 下载地址是网页，使用抓取的发布日期
        date = scraped_date or ''
        print(f"  下载地址为网页，大小不适用")
    else:
        # 下载地址是文件，获取大小和修改时间
        exists, size, date = check_url_follow(url)
        if not exists and size == 0:
            print(f"  ⚠️ 下载地址不可用")
        # 计算MD5
        if exists:
            md5 = get_file_md5(url)
            if md5:
                print(f"  MD5: {md5}")

    # 如果有抓取的发布日期且文件没有 Last-Modified，使用抓取的日期
    if scraped_date and not date:
        date = scraped_date

    return version, url, url, size, date, md5


def find_latest(product):
    """根据检测类型分发"""
    detect_type = product.get('detect_type', 'increment')

    if detect_type == 'redirect':
        version, full_url, param_url, size, date, md5 = detect_redirect(product)
    elif detect_type == 'fixed':
        version, full_url, param_url, size, date, md5 = detect_fixed(product)
    elif detect_type == 'scrape':
        version, full_url, param_url, size, date, md5 = detect_scrape(product)
    else:
        version, full_url, param_url, size, date, md5 = detect_increment(product)

    # 如果配置了 version_display，使用它作为显示版本号（URL中仍用检测到的版本）
    display_version = product.get('version_display', version)

    return {
        'name': product['name'],
        'name_cn': product['name_cn'],
        'icon': product.get('icon', ''),
        'icon_color': product.get('icon_color', ''),
        'category': product.get('category', '其他'),
        'version': display_version,
        'download_url': full_url,
        'download_url_with_params': param_url,
        'size': size,
        'size_mb': round(size / 1024 / 1024, 1) if size else 0,
        'last_modified': date,
        'md5': md5,
        'official_site': product.get('official_site', ''),
    }


def main():
    results = []
    for product in PRODUCTS:
        print(f"检测 {product['name_cn']} ({product['name']}) [{product.get('detect_type', 'increment')}]...")
        info = find_latest(product)
        print(f"  最新版: {info['version']}, 大小: {info['size_mb']} MB")
        results.append(info)
        time.sleep(1)

    data = {
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'products': results,
    }

    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n已保存到 {DATA_JSON}")
    print(f"更新时间: {data['updated_at']}")
    print(f"共 {len(results)} 个产品")


if __name__ == '__main__':
    main()
