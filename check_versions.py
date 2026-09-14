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
        'version': '22.6.1',
        'date': '2026-09-02',
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
        'version': '8.0.0110',
        'date': '2026-09-03',
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
        'date': '2026-09-13',
        'download_url': 'https://www.xyplorer.com/download/xyplorer64_full_noinstall.zip',
        'official_site': 'https://www.xyplorer.com/',
    },
    {
        'name': 'Microsoft Edge',
        'name_cn': 'Microsoft Edge',
        'icon': 'E',
        'icon_color': 'linear-gradient(135deg, #0078d4, #00bcf2)',
        'category': '浏览器',
        'detect_type': 'scrape',
        'check_url': 'https://raw.githubusercontent.com/Bush2021/edge_installer/main/readme.md',
        'version_regex': r'\*\*x64\*\*\s*\|\s*`(\d+\.\d+\.\d+\.\d+)',
        'download_url_regex': r'\*\*x64\*\*.*?\]\((https://[^)]+)\)',
        'version': '153.0.4234.32',
        'download_url': 'https://github.com/Bush2021/edge_installer/releases',
        'official_site': 'https://github.com/Bush2021/edge_installer',
    },
    {
        'name': 'Google Chrome',
        'name_cn': 'Google Chrome',
        'icon': 'C',
        'icon_color': 'linear-gradient(135deg, #4285f4, #34a853)',
        'category': '浏览器',
        'detect_type': 'scrape',
        'check_url': 'https://raw.githubusercontent.com/Bush2021/chrome_installer/main/readme.md',
        'version_regex': r'\*\*x64\*\*\s*\|\s*`(\d+\.\d+\.\d+\.\d+)',
        'download_url_regex': r'\*\*x64\*\*.*?\]\((https://[^)]+)\)',
        'version': '153.0.8010.37',
        'download_url': 'https://github.com/Bush2021/chrome_installer/releases',
        'official_site': 'https://github.com/Bush2021/chrome_installer',
    },
    {
        'name': 'NetEase Cloud Music',
        'name_cn': '网易云音乐',
        'icon': '网',
        'icon_color': 'linear-gradient(135deg, #e60026, #ff4d4f)',
        'category': '影音娱乐',
        'detect_type': 'increment',
        'base_version': '3.1.40.205461',
        'url_pattern': 'https://d8.music.126.net/dmusic2/NeteaseCloudMusic_Music_official_{ver}_64.exe',
        'param_format': '',
        'channel': '',
        'referer': 'https://music.163.com/',
        'official_site': 'https://music.163.com/#/download',
    },
    {
        'name': '360 Safe Browser 16',
        'name_cn': '360安全浏览器16',
        'icon': '360',
        'icon_color': 'linear-gradient(135deg, #00b42a, #00d68f)',
        'category': '浏览器',
        'detect_type': 'increment',
        'base_version': '16.3.1053',
        'url_pattern': 'https://sedl.360tpcdn.com/se/360se{ver}.64.exe',
        'param_format': '',
        'channel': '',
        'official_site': 'https://browser.360.cn/',
    },
    {
        'name': '360 Safe Browser 17',
        'name_cn': '360安全浏览器17',
        'icon': '360',
        'icon_color': 'linear-gradient(135deg, #00b42a, #00d68f)',
        'category': '浏览器',
        'detect_type': 'increment',
        'base_version': '17.1.1036',
        'url_pattern': 'https://sedl.360tpcdn.com/se/360se{ver}.64.exe',
        'param_format': '',
        'channel': '',
        'official_site': 'https://bbs.360.cn/thread-16184433-1-1.html',
    },
    {
        'name': '360 Extreme Browser',
        'name_cn': '360极速浏览器',
        'icon': '360',
        'icon_color': 'linear-gradient(135deg, #165dff, #4080ff)',
        'category': '浏览器',
        'detect_type': 'increment',
        'base_version': '23.1.1253',
        'url_pattern': 'https://sedl.360tpcdn.com/cse/360csex_{ver}.64.exe',
        'param_format': '',
        'channel': '',
        'official_site': 'https://chromex.360.cn/',
    },
    {
        'name': 'Topaz Photo',
        'name_cn': 'Topaz Photo',
        'icon': 'P',
        'icon_color': 'linear-gradient(135deg, #ff6b35, #f7931e)',
        'category': '图像处理',
        'detect_type': 'scrape',
        'check_url': 'https://community.topazlabs.com/c/topaz-photo/topaz-photo-releases/117',
        'detail_url_regex': r'https://community\.topazlabs\.com/t/[a-z0-9-]+/[0-9]+',
        'detail_url_index': 2,
        'version_regex': r'v(\d+\.\d+\.\d+)',
        'date_regex': r'article:published_time" content="([^"]+)"',
        'version': '1.7.0',
        'download_url': 'https://downloads.topazlabs.com/deploy/TopazPhoto/1.7.0/TopazPhoto-1.7.0.msi',
        'official_site': 'https://community.topazlabs.com/c/topaz-photo/topaz-photo-releases/117',
    },
    {
        'name': 'Topaz Gigapixel',
        'name_cn': 'Topaz Gigapixel',
        'icon': 'G',
        'icon_color': 'linear-gradient(135deg, #7b2ff7, #a855f7)',
        'category': '图像处理',
        'detect_type': 'scrape',
        'check_url': 'https://community.topazlabs.com/c/topaz-gigapixel/topaz-gigapixel-releases/128',
        'detail_url_regex': r'https://community\.topazlabs\.com/t/[a-z0-9-]+/[0-9]+',
        'detail_url_index': 2,
        'version_regex': r'v(\d+\.\d+\.\d+)',
        'date_regex': r'article:published_time" content="([^"]+)"',
        'version': '1.3.6',
        'download_url': 'https://downloads.topazlabs.com/deploy/TopazGigapixel/1.3.6/TopazGigapixel-1.3.6.msi',
        'official_site': 'https://community.topazlabs.com/c/topaz-gigapixel/topaz-gigapixel-releases/128',
    },
    {
        'name': 'Topaz Video',
        'name_cn': 'Topaz Video',
        'icon': 'V',
        'icon_color': 'linear-gradient(135deg, #ef4444, #f97316)',
        'category': '视频处理',
        'detect_type': 'scrape',
        'check_url': 'https://community.topazlabs.com/c/topaz-video/topaz-video-releases/122',
        'detail_url_regex': r'https://community\.topazlabs\.com/t/[a-z0-9-]+/[0-9]+',
        'detail_url_index': 2,
        'version_regex': r'v(\d+\.\d+\.\d+)',
        'date_regex': r'article:published_time" content="([^"]+)"',
        'version': '1.7.0',
        'download_url': 'https://downloads.topazlabs.com/deploy/TopazVideoStudio/1.7.0/TopazVideo-1.7.0.msi',
        'official_site': 'https://community.topazlabs.com/c/topaz-video/topaz-video-releases/122',
    },
    {
        'name': 'Adobe Flash Player',
        'name_cn': 'Adobe Flash Player',
        'icon': 'F',
        'icon_color': 'linear-gradient(135deg, #f0282f, #ff6b6b)',
        'category': '运行环境',
        'detect_type': 'scrape',
        'check_url': 'https://flash-player-links.pages.dev/',
        'version_regex': r'"version":\s*"([^"]+)"',
        'date_regex': r'"date":\s*"([^"]+)"',
        'version': '34.0.0.384',
        'download_url': 'https://flash-player-links.pages.dev/',
        'official_site': 'https://flash-player-links.pages.dev/',
    },
    {
        'name': 'IObit Uninstaller',
        'name_cn': 'IObit Uninstaller',
        'icon': 'I',
        'icon_color': 'linear-gradient(135deg, #ff6b35, #f7931e)',
        'category': '系统工具',
        'detect_type': 'fixed',
        'version': '16.0.0.34',
        'download_url': 'https://cdn.iobit.com/dl/iobituninstaller.exe',
        'official_site': 'https://www.iobit.com/en/advanceduninstaller.php',
    },
    {
        'name': 'WinSnap',
        'name_cn': 'WinSnap',
        'icon': 'W',
        'icon_color': 'linear-gradient(135deg, #667eea, #764ba2)',
        'category': '图像工具',
        'detect_type': 'increment',
        'base_version': '6.3.2',
        'url_pattern': 'https://www.ntwind.com/files/WinSnap_{ver}-setup.exe',
        'param_format': '',
        'channel': '',
        'date': '2026-09-10',
        'official_site': 'https://www.ntwind.com/blog',
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


def check_url(url, referer=None):
    """检测URL是否存在，返回 (exists, size, last_modified)
    不跟随重定向：302/301（如CDN跳转404页）视为文件不存在
    HEAD无Content-Length时用GET探测
    """
    headers = {'User-Agent': UA}
    if referer:
        headers['Referer'] = referer
    try:
        req = urllib.request.Request(url, method='HEAD', headers=headers)
        with _no_redirect_opener.open(req, timeout=10) as resp:
            size = resp.headers.get('Content-Length', '0')
            last_modified = resp.headers.get('Last-Modified', '')
            if resp.status == 200 and (not size or int(size) == 0):
                # HEAD无Content-Length，用GET探测
                try:
                    req2 = urllib.request.Request(url, headers=headers)
                    with _no_redirect_opener.open(req2, timeout=15) as resp2:
                        size = resp2.headers.get('Content-Length', '0')
                        if not size or int(size) == 0:
                            # 分块传输，读取实际大小
                            total = 0
                            while True:
                                chunk = resp2.read(65536)
                                if not chunk:
                                    break
                                total += len(chunk)
                            size = str(total)
                except Exception:
                    pass
            return resp.status == 200, int(size) if size and size.isdigit() else 0, last_modified
    except urllib.error.HTTPError:
        return False, 0, ''
    except Exception:
        return False, 0, ''


def check_url_follow(url, referer=None):
    """检测URL（跟随重定向），返回 (exists, size, last_modified)
    用于fixed模式，因为有些固定地址会302到CDN
    HEAD无Content-Length时用GET探测
    """
    headers = {'User-Agent': UA}
    if referer:
        headers['Referer'] = referer
    try:
        req = urllib.request.Request(url, method='HEAD', headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            size = resp.headers.get('Content-Length', '0')
            last_modified = resp.headers.get('Last-Modified', '')
            if resp.status == 200 and (not size or int(size) == 0):
                try:
                    req2 = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req2, timeout=20) as resp2:
                        size = resp2.headers.get('Content-Length', '0')
                        if not size or int(size) == 0:
                            total = 0
                            while True:
                                chunk = resp2.read(65536)
                                if not chunk:
                                    break
                                total += len(chunk)
                            size = str(total)
                except Exception:
                    pass
            return resp.status == 200, int(size) if size and size.isdigit() else 0, last_modified
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return True, 0, ''
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


def parse_date(date_str):
    """解析多种日期格式为 YYYY-MM-DD"""
    date_str = date_str.strip()
    # ISO格式: 2026-08-27T17:23:08+00:00
    m = re.match(r'(20\d{2}-\d{2}-\d{2})T', date_str)
    if m:
        return m.group(1)
    # 英文月份: September 9, 2026
    months = {'january':'01','february':'02','march':'03','april':'04','may':'05','june':'06',
              'july':'07','august':'08','september':'09','october':'10','november':'11','december':'12',
              'jan':'01','feb':'02','mar':'03','apr':'04','jun':'06','jul':'07','aug':'08','sep':'09','oct':'10','nov':'11','dec':'12'}
    m = re.match(r'([A-Za-z]+)\s+(\d{1,2}),?\s*(20\d{2})', date_str)
    if m:
        mon = months.get(m.group(1).lower(), '01')
        return f"{m.group(3)}-{mon}-{m.group(2).zfill(2)}"
    # 中文格式: 2026年09月09日
    date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
    # 斜杠格式
    date_str = date_str.replace('/', '-')
    return date_str


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
    referer = product.get('referer')

    # 先确认 base_version 存在
    url = product['url_pattern'].format(ver=current)
    exists, size, date = check_url(url, referer=referer)
    if exists:
        latest_size = size
        latest_date = date
    else:
        print(f"  ⚠️ 警告: 基础版本 {current} 不存在，可能已下架或网络异常")

    # 递增检测
    for _ in range(MAX_INCREMENT):
        next_ver = increment_version(current)
        url = product['url_pattern'].format(ver=next_ver)
        exists, size, date = check_url(url, referer=referer)
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
    # 网页链接不检测大小
    is_webpage = url.endswith('/') or '#' in url or '.html' in url or 'pages.dev' in url or 'update-history' in url
    if is_webpage:
        size = 0
        date = ''
    else:
        exists, size, date = check_url_follow(url)
        if not exists and size == 0:
            print(f"  ⚠️ 警告: 固定地址不可用，可能链接已失效")
    version = product.get('version', '最新版')
    return version, url, url, size, date, ''


def get_file_md5(url, max_retries=3, max_size_mb=500):
    """下载文件并计算MD5，返回md5十六进制字符串。支持重试。
    超过 max_size_mb 的文件跳过MD5计算（避免大文件下载过慢）
    """
    # 先 HEAD 请求获取文件大小
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA}, method='HEAD')
        with urllib.request.urlopen(req, timeout=15) as resp:
            size = int(resp.headers.get('Content-Length', '0'))
            if size > max_size_mb * 1024 * 1024:
                print(f"  文件过大({size/1024/1024:.0f}MB)，跳过MD5计算")
                return ''
    except Exception:
        pass

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
    """抓取模式：从官网页面抓取版本号、发布日期、下载链接
    支持两步抓取：列表页提取详情页URL → 详情页抓发布日期
    下载地址为网页时不计算MD5；为文件时计算MD5
    版本号优先使用配置默认值，官网抓取仅作参考
    """
    default_version = product.get('version', '未知')
    scraped_version = None
    scraped_date = None
    scraped_download_url = None

    # 从官网抓取版本号、发布日期、下载链接
    try:
        req = urllib.request.Request(product['check_url'], headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        # 两步抓取：如果配置了 detail_url_regex，从列表页提取详情页URL并访问
        detail_url_regex = product.get('detail_url_regex')
        if detail_url_regex:
            matches = re.findall(detail_url_regex, html, re.I)
            # 取第N个匹配（detail_url_index，默认1即第二个，跳过置顶帖）
            idx = product.get('detail_url_index', 1)
            if len(matches) > idx:
                detail_url = matches[idx]
                print(f"  详情页: {detail_url[:80]}...")
                try:
                    req2 = urllib.request.Request(detail_url, headers={'User-Agent': UA})
                    with urllib.request.urlopen(req2, timeout=20) as resp2:
                        html = resp2.read().decode('utf-8', errors='ignore')
                except Exception as e:
                    print(f"  ⚠️ 详情页访问失败: {e}")
            elif matches:
                detail_url = matches[0]
                print(f"  详情页(第1个): {detail_url[:80]}...")
                try:
                    req2 = urllib.request.Request(detail_url, headers={'User-Agent': UA})
                    with urllib.request.urlopen(req2, timeout=20) as resp2:
                        html = resp2.read().decode('utf-8', errors='ignore')
                except Exception as e:
                    print(f"  ⚠️ 详情页访问失败: {e}")

        # 抓取版本号（支持多捕获组，用.连接）
        regex = product.get('version_regex')
        if regex:
            m = re.search(regex, html, re.I)
            if m:
                groups = [g for g in m.groups() if g]
                if len(groups) > 1:
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
                scraped_date = parse_date(m.group(1))
                print(f"  发布日期: {scraped_date}")

        # 抓取下载链接
        dl_regex = product.get('download_url_regex')
        if dl_regex:
            m = re.search(dl_regex, html, re.I)
            if m:
                scraped_download_url = m.group(1)
                print(f"  抓取下载链接: {scraped_download_url[:80]}...")
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

    # 下载链接：优先使用抓取到的，其次用配置的
    url = scraped_download_url or product['download_url']

    # 获取文件信息（仅当下载地址是文件时）
    is_webpage = url.endswith('.html') or url.endswith('/') or 'download.html' in url or 'update-history' in url or 'pages.dev' in url
    size = 0
    date = ''
    md5 = ''

    if is_webpage:
        date = scraped_date or ''
        print(f"  下载地址为网页，大小不适用")
    else:
        exists, size, date = check_url_follow(url)
        if not exists and size == 0:
            print(f"  ⚠️ 下载地址不可用")
        if exists:
            md5 = get_file_md5(url)
            if md5:
                print(f"  MD5: {md5}")

    if scraped_date and not date:
        date = scraped_date

    # 配置的固定日期优先（当抓取不到时）
    if not date and product.get('date'):
        date = product['date']

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
