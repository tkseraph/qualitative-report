# 本地投研报告发布站

`site/` 是面向公网的独立静态内容区。它只接收人工批准的最终 HTML 报告，不直接暴露项目的 `output/`、年报 PDF、数据包或 Prompt。

## 发布流程

先预览发布元数据和安全检查结果，不写入站点：

```bash
.venv/bin/python scripts/publish_report.py \
  --report output/<公司目录>/<股票代码>_qualitative_report.html
```

确认报告允许公开后，再显式批准：

```bash
.venv/bin/python scripts/publish_report.py \
  --report output/<公司目录>/<股票代码>_qualitative_report.html \
  --approve
```

发布器会完成以下工作：

- 识别公司、股票代码、报告类型、日期、行业和短评级；
- 删除旧站点 canonical、Open Graph URL 和无效字体预加载；
- 拦截本地 API key、常见凭据格式、私钥、`file://` 和用户绝对路径；
- 给详情页增加“返回报告目录”入口；
- 写入 `site/content/reports.json` 并重建 `site/dist/`。

相同公司、类型和日期的报告默认不能重复发布。确认是更新版本时使用 `--replace`。

## 单独重建与本地预览

```bash
.venv/bin/python scripts/site_builder.py
.venv/bin/python -m http.server 8000 --directory site/dist
```

打开 `http://127.0.0.1:8000/`。首页按商业质量、投资策略和估值研究分类展示标题；点击标题进入独立详情页。

## 域名启用前后

域名未就绪时，`site/config.json` 中的 `base_url` 保持为空。构建器会输出 `noindex,nofollow` 和禁止抓取的 `robots.txt`，避免测试站被搜索引擎收录。

域名、ICP备案和 HTTPS 都完成后，再填写：

```json
{
  "base_url": "https://你的域名",
  "icp_number": "你的ICP备案号"
}
```

随后重新构建即可生成正式 canonical、Open Graph URL、`robots.txt` 和 `sitemap.xml`。
