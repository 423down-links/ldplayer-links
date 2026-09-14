#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常用软件最新版离线安装包自动检测脚本
从当前版本递增检测，找到最新可用版本
支持多产品配置，方便后续扩展
"""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JSON = os.path.join(BASE_DIR, 'data.json')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# 产品配置：支持任意段版本号、任意URL模式
PRODUCTS = [
    {
        'name': 'LDPlayer 9',
        'name_cn': '雷电模拟器 9',
        'icon': '9',
        'icon_color': 'linear-gradient(135deg, #ff6b35, #f7931e)',
        'category': '模拟器',
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
        'base_version': '25.1.13.1631',
        'url_pattern': 'https://down.sandai.net/thunder_pc/ThunderSetup{ver}up.exe',
        'param_format': '',
        'channel': '',
        'official_site': 'https://www.xunlei.com/',
    },
]

MAX_INCREMENT = 30  # 最多递增检测30个版本


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """禁止跟随重定向，302/301视为不存在"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

_no_redirect_opener = urllib.request.build_opener(NoRedirect)


def check_url(url):
    """检测URL是否存在，返回 (status, size, last_modified)
    不跟随重定向：302/301（如CDN跳转404页）视为文件不存在
    """
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': UA})
        with _no_redirect_opener.open(req, timeout=10) as resp:
            size = resp.headers.get('Content-Length', '0')
            last_modified = resp.headers.get('Last-Modified', '')
            return resp.status == 200, int(size), last_modified
    except urllib.error.HTTPError:
        # 302/301/404 等都视为不存在
        return False, 0, ''
    except Exception:
        return False, 0, ''


def increment_version(version):
    """递增版本号的最后一段，支持任意段数"""
    parts = version.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    return '.'.join(parts)


def find_latest(product):
    """从 base_version 开始递增检测，找到最新可用版本"""
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

    return {
        'name': product['name'],
        'name_cn': product['name_cn'],
        'icon': product['icon'],
        'icon_color': product['icon_color'],
        'category': product['category'],
        'version': latest,
        'download_url': full_url,
        'download_url_with_params': param_url,
        'size': latest_size,
        'size_mb': round(latest_size / 1024 / 1024, 1),
        'last_modified': latest_date,
        'official_site': product.get('official_site', ''),
    }


def main():
    results = []
    for product in PRODUCTS:
        print(f"检测 {product['name_cn']} ({product['name']})...")
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
