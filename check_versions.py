#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雷电模拟器最新版自动检测脚本
从当前版本递增检测，找到最新可用版本
"""

import json
import os
import time
import urllib.request
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JSON = os.path.join(BASE_DIR, 'data.json')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# 产品配置：主版本号、当前已知版本号、渠道号
PRODUCTS = [
    {
        'name': 'LDPlayer 9',
        'name_cn': '雷电模拟器9',
        'major': '9',
        'base_version': '9.5.37',
        'channel': '407594',
        'url_pattern': 'https://lddl01.ldmnq.com/download/leidian9/ldinst_{ver}.exe',
    },
    {
        'name': 'LDPlayer 14',
        'name_cn': '雷电模拟器14',
        'major': '14',
        'base_version': '14.0.27',
        'channel': '412570',
        'url_pattern': 'https://lddl01.ldmnq.com/download/leidian14/ldinst_{ver}.exe',
    },
]

MAX_INCREMENT = 20  # 最多递增检测20个版本


def check_url(url):
    """检测URL是否存在，返回 (status, size, last_modified)"""
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            size = resp.headers.get('Content-Length', '0')
            last_modified = resp.headers.get('Last-Modified', '')
            return resp.status == 200, int(size), last_modified
    except Exception:
        return False, 0, ''


def increment_version(version):
    """递增版本号的最后一段，如 9.5.37 -> 9.5.38"""
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

    # 生成带参数的完整下载链接（模拟官方链接格式）
    timestamp = int(time.time() * 1000)
    full_url = product['url_pattern'].format(ver=latest)
    param_url = f"{full_url}?v={timestamp}&n=ldinst_{latest}_ld_{product['channel']}_ld.exe"

    return {
        'name': product['name'],
        'name_cn': product['name_cn'],
        'version': latest,
        'download_url': full_url,
        'download_url_with_params': param_url,
        'size': latest_size,
        'size_mb': round(latest_size / 1024 / 1024, 1),
        'last_modified': latest_date,
        'channel': product['channel'],
    }


def main():
    results = []
    for product in PRODUCTS:
        print(f"检测 {product['name']}...")
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


if __name__ == '__main__':
    main()
