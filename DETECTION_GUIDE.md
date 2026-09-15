# 软件版本探测方式指南

## 探测方式总览

| 方式 | 适用场景 | 效率 | 准确度 | 代表软件 |
|------|----------|------|--------|----------|
| increment | URL含版本号，版本连续递增 | ⭐⭐⭐⭐⭐ | 高 | 雷电、迅雷、搜狗、360 |
| increment+skip | URL含版本号，版本可能跳过 | ⭐⭐⭐⭐ | 高 | 微信(跳过4.1.14) |
| redirect | 固定地址302跳转到版本文件 | ⭐⭐⭐⭐⭐ | 高 | XMind |
| fixed | 固定地址始终最新版 | ⭐⭐⭐⭐⭐ | 中 | IObit、网易云 |
| scrape | 从网页抓取版本/日期/下载链接 | ⭐⭐⭐ | 中 | Edge、Chrome、Xshell |
| PE版本 | 从exe文件.rsrc段读取FileVersion | ⭐⭐⭐⭐ | 高 | 微信、YY、360浏览器 |
| NSIS版本 | 从NSIS安装包内install.7z读取版本文件夹 | ⭐⭐⭐ | 极高 | 微信 |
| MD5校验 | 下载文件计算MD5 | ⭐ | 高 | 小文件(<100MB) |

## 各方式详细说明

### 1. increment（递增检测）
**原理**：从base_version开始逐个递增版本号，检测URL是否存在(HTTP 200)
**配置**：
```python
{
    'detect_type': 'increment',
    'base_version': '9.5.37',
    'url_pattern': 'https://example.com/software_{ver}.exe',
}
```
**优点**：简单高效，只需HEAD请求
**缺点**：版本号不连续时会漏检（已改进为跳过最多5个不存在版本）
**适用**：版本号在URL中且有规律的软件

### 2. increment + PE版本探测
**原理**：increment检测到大版本后，从PE文件.rsrc段读取四段版本号
**配置**：
```python
{
    'detect_type': 'increment',
    'base_version': '4.1.15',
    'url_pattern': 'https://example.com/software_{ver}.exe',
    'pe_version': True,
}
```
**优点**：可获取安装包内部精确版本号（如4.1.15.1000）
**缺点**：需下载PE头和.rsrc段（约200KB）
**适用**：安装包PE头版本与显示版本不同的软件

### 3. increment + NSIS版本探测
**原理**：increment检测到版本后，解析NSIS安装包内install.7z的版本号文件夹
**配置**：
```python
{
    'detect_type': 'increment',
    'base_version': '4.1.15',
    'url_pattern': 'https://example.com/software_{ver}.exe',
    'nsis_version': True,
    'pe_version': True,  # 兜底
}
```
**优点**：可获取安装后软件的精确版本号（如微信4.1.15.9）
**缺点**：需下载NSIS头部3MB+install.7z头尾160KB，需7z命令
**适用**：NSIS打包且install.7z内含版本号文件夹的软件（微信）
**探测流程**：
1. 下载PE头(1KB) → 获取overlay偏移
2. 下载NSIS头部(3MB) → 搜索7z签名获取install.7z偏移
3. 下载install.7z头部(32B) → 读取next_header_offset计算精确大小
4. 下载install.7z头尾(32KB+128KB) → 构造文件用7z列出内容
5. 提取第一个文件夹名称作为版本号
**总下载量**：约3.2MB（vs 完整下载244MB）

### 4. redirect（重定向检测）
**原理**：访问固定地址，从302 Location头提取版本号和下载链接
**配置**：
```python
{
    'detect_type': 'redirect',
    'check_url': 'https://example.com/download',
    'version_regex': r'(\d+\.\d+\.\d+)',
}
```
**优点**：一次请求获取版本和下载链接
**缺点**：依赖服务器返回302
**适用**：固定下载地址会302跳转到版本文件的软件

### 5. fixed（固定地址）
**原理**：固定地址始终指向最新版，版本号手动维护
**配置**：
```python
{
    'detect_type': 'fixed',
    'version': '16.0.0.34',
    'download_url': 'https://example.com/latest.exe',
}
```
**优点**：URL不变，用户收藏可用
**缺点**：版本号需手动更新
**适用**：官方提供固定最新版地址的软件

### 6. scrape（网页抓取）
**原理**：请求官方页面，用正则提取版本号、日期、下载链接
**配置**：
```python
{
    'detect_type': 'scrape',
    'check_url': 'https://example.com/download',
    'version_regex': r'最新版[:：]\s*(\d+\.\d+\.\d+)',
    'date_regex': r'(\d{4}-\d{2}-\d{2})',
    'download_url_regex': r'(https?://[^\s"]+\.exe)',
    'version': '1.0.0',  # 默认版本优先
}
```
**两步抓取**（Topaz社区）：
```python
{
    'detail_url_regex': r'(https://community\.example\.com/t/[^"]+)',
    'detail_url_index': 0,
}
```
**优点**：可获取官方页面的所有信息
**缺点**：页面结构变化会失效，需维护正则
**适用**：版本信息在网页上的软件

### 7. MD5校验
**原理**：下载完整文件计算MD5
**限制**：>100MB跳过，>500MB强制跳过
**适用**：小文件校验

## 新增软件探测方式选择流程

```
1. 官方是否提供固定下载地址？
   ├─ 是 → 地址是否302跳转？
   │       ├─ 是 → redirect模式
   │       └─ 否 → fixed模式（版本手动维护）
   └─ 否 → 下载地址是否含版本号？
           ├─ 是 → increment模式
           │       ├─ 安装包是NSIS且install.7z有版本文件夹？→ 加nsis_version
           │       ├─ PE头版本与显示版本不同？→ 加pe_version
           │       └─ 版本号可能不连续？→ 已自动支持跳过
           └─ 否 → 版本信息是否在网页上？
                   ├─ 是 → scrape模式
                   └─ 否 → 需人工研究其他方式
```

## 效率优化记录

| 优化项 | 优化前 | 优化后 | 提升 |
|--------|--------|--------|------|
| increment跳过版本 | 遇404停止 | 跳过最多5个 | 微信可检测到跳过版本 |
| 微信版本探测 | 手动维护4.1.13.65 | NSIS自动获取4.1.15.9 | 全自动 |
| NSIS版本探测 | 下载244MB完整包 | 下载3.2MB头尾 | 98.7%流量节省 |
| 单软件超时 | 无（一个卡住全部卡住） | 45秒超时+重试2次 | 可靠性提升 |
| 检测失败处理 | 覆盖为空 | 保留上次成功数据 | 数据不丢失 |
| MD5计算 | 全文件下载 | >100MB跳过 | 大文件不超时 |

## 已知限制

1. **QQ音乐**：防盗链严格，所有Referer返回403，sign无法自动生成，下载地址指向官网页
2. **Topaz系列**：Cloudflare 403拦截Python urllib，大小用固定值，日期从社区帖子抓取
3. **Xshell**：下载需邮箱接收随机地址，版本从更新历史页抓取
4. **Flash Player**：下载地址是网页，版本从flash-player-links页面抓取
5. **XYplorer**：官网偶尔超时，版本用配置默认值优先
