# 雷电模拟器最新版下载 - LDPlayer Latest Downloads

自动检测雷电模拟器9和雷电14的最新版本，提供官方CDN直链下载。

## 功能

- **自动检测版本**：从已知版本递增扫描官方CDN，找到最新可用版本
- **官方CDN直链**：直接使用 `lddl01.ldmnq.com` 官方下载地址
- **每日自动更新**：GitHub Actions 每日北京时间8:00自动检测
- **支持下载工具**：直链支持 IDM 等下载工具

## 访问地址

https://423down.github.io/ldplayer-links/

## 下载链接格式

- 雷电9：`https://lddl01.ldmnq.com/download/leidian9/ldinst_{版本号}.exe`
- 雷电14：`https://lddl01.ldmnq.com/download/leidian14/ldinst_{版本号}.exe`

## 当前版本

| 产品 | 最新版本 | 大小 |
|------|----------|------|
| 雷电模拟器9 | 9.5.37 | 574.1 MB |
| 雷电模拟器14 | 14.0.27 | 709.7 MB |

## 文件说明

- `index.html` - 主页面
- `data.json` - 版本数据
- `check_versions.py` - 版本自动检测脚本
- `embed_data.py` - 将数据嵌入HTML
- `.github/workflows/update.yml` - 每日自动更新工作流
