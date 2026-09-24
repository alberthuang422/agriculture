# ISO 食糖数据仓库（data/sugar/iso）

ISO = International Sugar Organization（国际糖业组织），全球糖市最重要的政府间机构，其季度市场展望（QMO）、月度市场报告与官方世界糖平衡表（World Sugar Balance memo）是全球糖供需的权威口径之一。

**范围**：2011/12 ~ 2026/27 全球食糖平衡表 + 2025/26 季完整修订轨迹（每一期 vintage 都保留）。

## 收录内容

| 文件 | 内容 |
|---|---|
| `iso_qmo_vintage.json` | **核心**：QMO 历次 vintage 全球平衡表追踪库（2025/26 季5个修订点 + 2026/27 首版 + 2024/25 修订链 + **2015/16、2016/17 早期修订链** + 2011-2027 官方最新序列 + 交叉机构共识） |
| `iso_qmo_vintage.csv` | 2025/26 季修订轨迹平铺表，pandas/Excel 直接用 |
| `iso_world_balance_2010_2026.csv` | **2011/12~2026/27 全球平衡表官方最新序列**（产/消/产销差/进出口/库存/库消比） |
| `iso_balance_vintage_matrix.csv` | surplus/deficit × 8 个 vintage 矩阵（千吨），直观看到每季咋修订 |
| `iso_balance_raw_matrix.json` | 8 期官方 PDF 全部指标的完整矩阵 |
| `early_vintage_matrix_2015_16_2023_24.csv` | **2015/16~2023/24 × 28 个早期发布期次的 surplus/deficit 修订矩阵**（千吨)，构建自 balance_pdfs/historical/ 官方原文 |
| `early_vintage_matrix_2015_16_2023_24.json` | 同上修订链的 JSON 版（并入核心库） |
| `balance_pdfs/` | **官方 World Sugar Balance memo PDF 存档**：主目录 8 期（Nov-2024 ~ Aug-2026，最新回溯视角）；`historical/` 子目录 28 期（2017-02 ~ 2024-08，**当年发布视角**，官方一手） |
| `headlines/qmo_*.md` | 官方 HEADLINES 全文（Nov-2025 / Feb-2026 / May-2026 / Aug-2026） |
| `market_reports/market_report_synopses.md` | 月度 Market Report 公开摘要（Nov/Dec 2025, Aug 2026） |

## 关键口径（务必遵守）

1. **市场年标签**：ISO 用 10 月-次年 9 月（October/September）作物年；"2025/26" 即该口径，与中文媒体"25/26 榨季(4月-3月)"不同。
2. **单位**：CSV 为百万吨（tel quel/raw）；矩阵 CSV 为千吨。
3. **balance = production − consumption**（产销差），≠ 贸易盈余（trade surplus）。
4. **库存/库消比口径发生过两次变化**：
   - 旧口径（2025/26 及以前，约 50-52%）→ 修订口径（May-2026 起 "shares methodology"：2025/26 为 44.15%，另报调整后 <42.4% 15年低）
   - **2026-08 起官方暂停发布库存**（ISO 正全面重审全球库存数据，结果 2026 年鉴发布）。因此最新期（2024/25-2026/27）end_stocks 为空。
   - 任何跨期比较必须先对齐口径。
5. **回溯修订**：ISO 会回溯修正历史年份——典型如 2022/23 从旧口径 +0.31 翻转为 −1.87 Mt、2023/24 从 +2.04 修正至 −0.25。用最新官方值做历史序列时，须知这些是"今天的视角"。

## 付费墙边界（已核实）

| 内容 | 价格 | 本库能拿到什么 |
|---|---|---|
| **World Sugar Balance memo PDF**（逐国+全球，各期 QMO 同期发布） | **官方 memo 免费**（购买版才 £170） | **完整存档 36 期 PDF**（本库 balance_pdfs/，其中 28 期早期 + 8 期最新；2015-16 当年期次官网无存档，见下） |
| QMO 全文（约 60 页） | £250/期 | HEADLINES 页全文（已存 4 期） |
| Monthly Market Report 全文 | £260/年订阅 | 官网公开的"The Market in [Month]"摘要 |
| 首页 ISA Daily Price / White Sugar Index | 免费 | 已确认 2026-09-03：ISA 18.52 c/lb, 白糖指数 525.45 $/T |

### 历史期次可得性（已核实 2026-09-24）

官网 `isosugar.org/content/memo/`（及 archive 镜像）公开存档的 memo 最早到 **2017-02**。
- **可下载**：2017-02 ~ 2024-08，共 28 期（已存 `balance_pdfs/historical/`）。
- **官网无存档**：2015-02 ~ 2016-11 共 8 期（2015 年 4 期 + 2016 年 4 期）——`world_sugar_balance_<month>_<year>.pdf` 在 www 与 archive 双源均 **404**。
- **影响**：2015/16、2016/17 两季最早的"当年发布 memo"拿不到原文，但它们的修订轨迹**已从 2017-02 起的期次完整重建**（2015/16：2017-02 初见 −5.36 → 最终 −6.46 Mt；2016/17：−5.87 → −3.61 Mt），见 `early_vintage_matrix_*`。
- 2015 年 4 期（2015-02/05/08/11）是 **2015/16 季内的发布期**——官网缺失意味着 2015/16 季内首次发布值不可考，只能从 2017 年起的回溯列取。

## 更新方法

1. QMO 每年 2/5/8/11 月发布。发布后到官网 `isosugar.org/content/memo/world_sugar_balance_<month>_<year>.pdf` 下载当期 PDF 到 `balance_pdfs/`（**官方公开，无需会员**）。
2. 把第 2 页全球汇总数字追加进 `iso_qmo_vintage.json`（`vintages` / `revision_timeline_*` / `official_vintage_matrix`）。
3. 复制当期 HEADLINES 全文到 `headlines/`。
4. 复核官方是否恢复发布库存数据（Aug-2026 起暂停）。

## 备注：ISA Daily Price 快照（2026-09 初）

- 2026-09-03: ISA Daily Raw Sugar 18.52 c/lb；15 日均价 18.15 c/lb；White Sugar Index 525.45 $/T
- 来源：isosugar.org 首页（抓取日期 2026-09-24）

## 待办 / 可扩展

- [ ] Nov-2026 QMO 发布后：核对官方是否恢复库存 + 下载当期 memo PDF
- [ ] 若需与 USDA/StoneX/Czarnikow/Green Pool 对照，用本项目已有 `psd_sugar_all.csv` + 本库 `cross_institution_*` 字段
- [ ] 若需要逐国平衡表：本库 PDF 内含全部国家明细页，可进一步解析成逐国面板
- [ ] 2015/16、2016/17 的"季内首版"值：官网缺 2015-02~2016-11 memo，可尝试其他镜像或媒体转述补齐（低优先级）