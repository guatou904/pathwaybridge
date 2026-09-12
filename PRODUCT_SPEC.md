# PathwayBridge — PRODUCT_SPEC

更新 2026-09-12：**ACTIVE / GitHub 0.1.0a1 预发布**。用户授权接着做第二个项目；BatchLens v0.1.0 工程交付门已满足，转维护。本项目承担唯一大型实现席位。独立科学评审与用户对照试验仍待完成，不把 alpha 当作已验证正式产品。

## 定位与用户

用户确认：把 DEG + 单细胞 + 空间 + 代谢物映射到同一条代谢通路，来源于当前 PPP（磷酸戊糖途径）研究。核心用户是需要把不同组学结果放在共同反应背景中解释的 biomedical 研究者；次要用户是帮助复核分子映射与结论的计算合作者。

任务：拿到多个分析结果表时，能知道每个观测对应哪条反应、来自哪个物种/细胞类型/空间区域/比较，哪些证据方向一致、冲突、缺失或存在歧义。不把四张独立富集图简单拼成一个 dashboard。

## 候选差异化

跨组学映射已有 [pyMultiOmics/GraphOmics](https://github.com/glasgowcompbio/pyMultiOmics)，多组学通路分析已有 [ReactomeGSA](https://github.com/reactome/ReactomeGSA)。增量假设是 **保留细胞/空间 context、反应级映射歧义、每个原始数值的出处**，帮助用户撰写可核对的 PPP 解释。尚未证明现有工具不能满足；先与真实 PPP 手工表对照。

## 已实现的受限 MVP

- 小鼠（NCBI taxon 10090）、PPP 的 7 条精选反应、固定版本的 UniProt 2026_03 注释适配。第二条转酮醇酶反应等缺失范围在报告首页明确列出。
- 输入为已完成分析的 CSV/TSV：DEG 的 ID/effect/adjusted p；细胞类型或空间区域的同类汇总；代谢物 ID/effect/assay context。允许部分模态缺失。
- 标准化实体 ID，保留一对多映射；每条映射带来源、版本、置信类别和人工复核状态。
- 输出 reaction/pathway evidence table、歧义/未映射清单、带 context 的通路视图和离线报告。
- 不跨模态平均 p 值、不把 expression 与 metabolite abundance 拼成统一 activation score。

非目标：FASTQ 到 DEG、scRNA preprocessing、空间配准、全数据库知识图谱、跨物种自动推断、代谢流/通量估计、因果机制证明、通用富集算法重写、自动论文写作、LLM 自动纠正 ID。

## 科学契约

每条 evidence 至少有 `source_id, modality, entity_id, namespace, species, cell_type/region, contrast, effect_type, value, unit, source_row, mapping_version`。缺失 context 明确 unknown；不同实验/不同 units 不直接当成配对数据。

基因表达上调、酶蛋白变化、代谢物积累分别展示；不能由三者直接推出 PPP flux 增加。代谢物异构体、同名别名和细胞 compartment 保留歧义。BatchLens 结果仅作可选附件，不能代替各实验自身设计审查。

## 验证与风险

本轮已核对真实 PPP 结果的物种、列结构和比较方向，并在本地对 490 条记录做回验；公开 demo 使用合成数据。建立了对照固定来源注释的自动化检查，尚未取得独立人工评审的 10–20 条 gold set，也尚未实际对比 pyMultiOmics、ReactomeGSA 和 spreadsheet 的用户任务耗时。验收重点是 ID 正确、context 不丢、歧义不隐藏，而非图是否漂亮。

工程 alpha 已交付：clean install、测试、README、demo、实际 Actions 和 GitHub 预发布均有证据。稳定版验收仍需两位实际使用者完成来源追溯、独立人工 gold mapping 评审和对照任务验证；这些尚未达到。

最大 scope creep：一次覆盖四种原始数据格式和所有通路库。收窄方式：输入只接受上游标准结果表，不承担上游分析；PPP 完整走通后才讨论第二条通路。
