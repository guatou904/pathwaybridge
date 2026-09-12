# PathwayBridge — architecture draft

更新 2026-09-12；ACTIVE / 0.1.0a1 已在本地实现。本文区分实际首版与后续扩展。

## 数据流

结果表 → schema 校验 → namespace/species 显式解析 → 版本化 entity/reaction mapping → context-preserving evidence table → 静态通路视图 + JSON/TSV + provenance。

实际首版使用 Python 3.11+ 标准库：argparse、csv、Decimal、hashlib、importlib.resources 和 html escaping。无需 pandas/Pydantic/Jinja2 运行依赖；表结构固定、无需矩阵计算，因此用显式字段校验即可。JSON 参考、HTML/CSS/JS 模板和 SVG 随包分发，离线运行。开发依赖用 uv.lock 固定。

## 数据模型

`Entity`（ID/namespace/species/compartment）；`Reaction`（来源/版本/实体角色）；`Mapping`（输入 ID、候选集合、来源、是否人工确认）；`Evidence`（模态、context、比较、统计量类型、原始行/文件 hash）；`PathwayView`（展示选择，不能重算统计量）。

一个基因可映射多个反应，一个代谢物名可对应多个候选；没有唯一映射时返回 ambiguous，不静默挑第一个。unsupported species/namespace 不自动转换。未映射数目必须进入报告首页。

每种上游来源一个小 adapter，只转表不做分析。单细胞和空间输入以 cell type/region 汇总结果体现；不解析 h5ad、空间图像或原始代谢质谱。数据库下载独立、显式、固定版本，MVP 可离线。

## 模块与仓库计划

```text
pathwaybridge/
  src/pathwaybridge/{core.py,report.py,cli.py}
  src/pathwaybridge/resources/{ppp_mouse.json,report.html,report.css,report.js,demo/}
  tests/test_core.py  scripts/{build_mapping,fetch_reference,package_smoke}.py
  docs/{input-contract,mapping-policy,interpretation,data-sources,validation-record}.md
  pyproject.toml  README.md  LICENSE  CITATION.cff
  .github/workflows/{ci,release}.yml
```

只交换标准文件；不依赖 BatchLens 或 ClaimMatrix 的 Python 包。共享来源字段约定，但自身维护 reaction schema。未来两工具确实复用后再讨论公共库。

## 测试与主要取舍

人工 gold mapping 覆盖同名异构体、species 冲突、一对多/无映射、同一实体不同 context 的反向变化。数值不变性测试确保 report 没有偷偷合并 effect/单位。快照核验 node 标签与原始 evidence 对应。

默认完整保留证据，不按所谓“可信度最高”自动删行；同一实验的多个输出需 provenance 去重，避免重复当独立证据。对错误映射的防护优先于自动覆盖更多数据库。

## 实际 CLI 与输出

`init --out` 生成合成模板；`validate --manifest` 校验；`build --manifest --out` 生成报告；`demo --out` 跑完整例。现存输出目录一律拒绝，不提供覆盖或递归清理选项。

JSON 保存原始字段字符串，TSV 保留效应字符串并对可能触发电子表格公式的文本加前导撇号。物种/namespace 不支持时保留记录并标明状态；格式/数值错误返回 exit 2。输入文件 SHA256 + 记录编号定位来源，额外保留记录结束的物理行号。HTML 使用严格 CSP 和边界转义；筛选脚本只操作已有 DOM，不发起网络请求。
