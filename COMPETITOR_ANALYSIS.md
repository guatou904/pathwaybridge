# PathwayBridge — competitor analysis

2026-09-11；一手资料 desk research，无实际跑分/用户访谈。用户需求来自 PPP 项目，具体物种、格式与手工工作量尚未获取。

| 工具 / 来源 | 已有价值 | PathwayBridge 必须证明的增量 |
|---|---|---|
| [ReactomeGSA](https://github.com/reactome/ReactomeGSA) | 比较多组学 gene set analysis，提供 R 客户端 | 不以“多组学通路比较”声称创新；验证反应级证据出处与 context 是否更适合 PPP |
| [pyMultiOmics](https://github.com/glasgowcompbio/pyMultiOmics) / [GraphOmics](https://github.com/glasgowcompbio/GraphOmics) | transcript/protein/metabolite 数据关联与通路探索 | 最近竞品；分子跨组学映射本身已存在，不能只换 UI |
| [GSEApy](https://github.com/zqfang/GSEApy) | Python gene set enrichment 与可视化 | 作为已有上游结果来源；不重写 enrichment |
| [decoupler](https://github.com/scverse/decoupler) | omics enrichment/activity inference 工具生态 | 保留其已有结果及方法 provenance；自己的通路图不能冒充更强的 activity 方法 |
| [DecoPath](https://decopath.scai.fraunhofer.de/) | 通路富集结果比较 | “跨数据库比较”也不是空白，不进入首版 |
| 手工 PPP 图 + spreadsheet | 灵活，直接保留研究者解释 | 实际最低成本基线；要减少反复追 ID、丢 context 和误覆盖 |

PyPI 当日 JSON 快照：[gseapy](https://pypi.org/project/gseapy/) 1.3.1，Python >=3.9；[decoupler](https://pypi.org/project/decoupler/) 2.2.0，Python >=3.11；[pyMultiOmics](https://pypi.org/project/pymultiomics/) 可发现。没有安装实测，未来依赖版本须重新解析。

GitHub API 快照：ReactomeGSA 未归档、最近 push 2026-06-12；pyMultiOmics 未归档、最近 push 2023-04-13。更新时间不代表功能质量或项目被放弃；旧工具也可能完全满足任务。

独立价值判断：**有真实用户任务，但差异化待核验。** 启动前必须逐条比较 PPP 的 ID 歧义、reaction 映射、cell/region context、原始结果追溯。若 pyMultiOmics 加一个 exporter 足够，则优先上游扩展或 recipe。

技术/数据风险：通路库版本、分子别名、物种与 compartment；数据库使用与再分发条件须单独核验，不能因客户端开源就把所有映射数据自由打包。没有审核条款前只计划可插拔本地映射表。


## 2026-09-12 启动复核

再次查阅 [pyMultiOmics 官方说明](https://github.com/glasgowcompbio/pyMultiOmics) 和 [ReactomeGSA 官方说明](https://github.com/reactome/ReactomeGSA)：前者已经用 Reactome 将多种分子映射到反应/通路并展示分析，后者明确支持多物种、多组学比较及单细胞分析。因此本项目不以“首次多组学整合”或更强通路分析为定位。

当前实现只检验一个窄假设：固定版本的离线 evidence ledger，保留每条原始字符串、cell/region/experiment context、候选歧义及上游排除状态，是否比手工反复追表更省事。本轮 490 条本地输入回验说明这条文件转换链可工作，但并不证明用户价值优于已有工具。未安装/运行竞品进行 head-to-head，未取得用户耗时数据。

对照任务拟用同一份合成案例：找到相反区域的 Pgd 证据、识别 Tkt 历史别名、区分 NADP(H) 氧化还原候选、追到原始行、识别重复导出。记录各工具是否支持、所需操作数、是否丢字段和人工修正时间。不得把未经测量的格子填写为“不支持”。
