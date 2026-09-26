# 全球棉花市场：生产、贸易格局与权威数据源总结

> 整理日期：2026-09-25
> 来源：用户提供资料整理归纳

---

## 一、全球棉花生产与贸易格局

### 1. 主要生产国（前五大占全球总产量 75%～80% 以上）

| 国家 | 特点 | 备注 |
|------|------|------|
| 中国 | 产量全球前列（集中于新疆），消费远超产量 | 全球最大进口国，需大量进口 |
| 印度 | 种植面积全球最大，产量常年前两名 | 品种涵盖短绒至长绒棉 |
| 美国 | 第三大生产国 | 机械化程度高，品质标准化强 |
| 巴西 | 近年来产量增长最快（马托格罗索州为主） | 单产高、品质优 |
| 巴基斯坦 | 传统生产大国 | 多用于国内纺织，进口依赖度上升 |

其他生产国：乌兹别克斯坦、澳大利亚、土耳其、贝宁、喀麦隆、马里等。

### 2. 主要出口国（核心供给端，集中度极高）

- **巴西 & 美国**：两大绝对主力，合计控制全球出口"半壁江山"（近年巴西多个月份/年份出口量赶超美国）
- **澳大利亚**：出口高品质、强力高的棉花，主要面向东亚、东南亚纺织企业
- **西非国家（C4 及周边）**：贝宁、布基纳法索、马里、科特迪瓦等，绝大部分棉花用于出口
- **印度**：出口量受国内政策、纺织需求及 MSP（最低支持价）调控，波动较大

### 3. 主要进口国（核心需求端）

- **中国**：全球最大棉花进口国
- **越南、孟加拉国、巴基斯坦、土耳其、印度尼西亚**：全球纺织产业转移主要接收国，原料进口需求强劲

---

## 二、权威统计与供需分析机构

> 棉花没有白糖 ISO 那样的唯一绝对权威，由国际组织、政府农业部门、行业协会与商业资讯公司共同构成统计体系。

### 1. 类似 ISO / ISMA 的核心官方与行业组织

| 机构 | 定位 | 核心数据 |
|------|------|----------|
| **ICAC**（国际棉业咨询委员会） | 类似白糖 ISO，联合国认可的唯一政府间棉花组织（总部华盛顿） | 《World Cotton Market Outlook》、全球月度供需平衡表（产量/消费/期末库存/价格预测） |
| **CAI**（印度棉花协会） | 类似印度白糖 ISMA，印度最权威行业数据源 | 各邦产量（Crop Estimates）、上市进度（Arrivals）、国内消费及出口预估 |
| **CCI**（印度棉花公司） | 印度政府背景收储调控机构 | MSP 收购执行、政府库存、拍卖计划、出口配额政策 |

### 2. 国际最核心的供需预测报告（必看）

**USDA（美国农业部）** — 全球棉花交易员最看重，地位甚至部分超越 ICAC

- **WASDE**（全球农业供需评估报告）：每月发布，覆盖各主产国/进口国的产量、消耗量、进口量、出口量、期末库存
- **Export Sales Report**（每周出口销售报告）：每周四发布，统计美国棉花对各国签约量与装运量，追踪短期出口情绪和需求强弱的"风向标"

### 3. 主要产区本土权威机构

| 国家 | 机构 | 数据内容 |
|------|------|----------|
| 中国 | **CCA**（中国棉花协会）、**NCMSS**（国家棉花市场监测系统） | 种植面积、新疆采摘/加工/检验进度、国内供需平衡表、进口配额动态 |
| 巴西 | **CONAB**（国家商品供应公司）、**ABRAPA**（棉花生产商协会） | CONAB：月度播种面积/单产/总产预估；ABRAPA：采摘、出厂装运、出口跟踪 |
| 澳大利亚 | **ABARES**（农业资源经济科学局） | 季度与年度产销预测 |

### 4. 商业资讯与报价机构

- **Cotlook**（英国棉展望公司）：发布 **Cotlook A 指数**（全球棉花现货贸易基准定价参考），提供全球供需预测报告
- **ICE**（洲际交易所）：棉花 2 号期货（Cotton No. 2）挂牌交易所，提供交割库库存（Certificated Stocks）等交易数据

---

## 三、快速对照：数据源优先级建议

1. **日常盯盘/短期需求**：USDA Export Sales Report（每周四）+ ICE 交割库存
2. **月度供需定调**：USDA WASDE + ICAC 月报 + CAI（印度）
3. **中国国内动态**：CCA / NCMSS（加工检验进度、配额政策）
4. **巴西产量与出口**：CONAB + ABRAPA
5. **现货定价基准**：Cotlook A 指数
6. **持仓情绪**：CFTC COT（周五 15:30 ET 发布，数据日为当周二）

---

## 四、本地已落数据清单（`data/cotton/`，2026-09-25 抓取）

| 文件 | 内容 | 口径/单位 | 更新方式 |
|------|------|-----------|----------|
| `usda_psd_cotton_major_countries.csv` | 17 个主产国/出口国/进口国 1960–2026 供需（产量/进口/出口/国内消费/期末库存/库消比） | 千 480 磅包（1 包=0.217724 吨）；库消比分母=Domestic Use | 重跑 `scripts/fetch_cotton_psd.py` |
| `usda_psd_cotton_world.csv` | 全球加总供需 + 库消比 | 同上；World=135 个互斥实体直接求和（无欧盟聚合行） | `scripts/fetch_cotton_world.py` |
| `usda_psd_cotton_world_exchina.csv` | **剥离中国**库存与库消比（分子分母均剔除中国） | 同上；2026 = 43.49%（注意：早期笔记里的 28.5% 是"剥离后库存÷未剔中国的全球消费"口径，与本文件不一致，以本文件为准） | 同上 |
| `worldbank_cotlook_a_monthly.csv` | Cotlook A 指数月度价格 1960-01～2025-12（792 期） | $/kg（历史峰值 2011-03 = $5.06 ≈ 230 美分/磅） | World Bank Pink Sheet 月度更新，注意序列滞后约 1 个季度 |
| `zce_cotton_CF0_daily.csv` | 郑棉期货主连日线 2005-01-04～2026-09-24（5288 根） | 元/吨（数据源：新浪 InnerFuturesNewService，symbol=CF0） | `data/_tmp/cf0.jsonp` 抓取命令可复用 |
| `cftc_cotton2_cot_2026.csv` | ICE 棉花 2 号 COT 周度持仓 2026 全年（37 期，倒序） | 手；含商业/非商业/总报告持仓与 OI | 换年份数字重下 `deacot{YYYY}.zip` |
| `fundamentals/cotton/us_cotton_esr_20260925/` | 美棉 ESR 周度出口同期对比：12 大买家当季（2026/27）逐周累计装运/净签约/在手订单 + 近 5 年度同期全轨迹 + 5 年均值（ESRQS Comparison5YearReport）+ 年度序列 | 千包（running bales）；同期点=各 MY 第 7 周 | 重跑 `scripts/fetch_cotton_esr.py`（apiEndpoint/参数见下"ESRQS 通道"） |

**ESRQS 数据通道（2026-09-25 实测可用，美棉周度出口查询首选）**：
- 基址 `https://apps.fas.usda.gov/esrqs/api`。匿名 token：POST `/token`（form 表单 `client_id=eAuth_Client&client_secret=00000000-0000-0000-0000-00000000000000000000-0000-0000-0000-000000000000&grant_type=client_credentials`），之后带 `Authorization: Bearer <token>`。
- 五年同期对比：`GET /reports/Comparison5YearReport?CommodityId=27&DestinationCountryCode=<国别码>&ReportCode=<10周出口|20累计出口|30周净销|40累计净销|50在手订单>`；返回当季逐周 + yearAgo1..5（往 5 个 MY 同周）+ 5 年均值。棉花 CommodityId=27（All Upland），国别码：中国 5700、越南 5520、巴基斯坦 5350、孟加拉 5380、土耳其 4890、墨西哥 2010、印度 5330、印尼 5600 等（`/lookups/ActiveCountries?WeekEndingDate=<yyyy-mm-dd>` 全表）。注意：该接口**无全国合计**（合计需逐国加总，12 大买家≈全国 89%）。
- 全国同期快照：`GET /reports/GetArchivedWeeklyReportsList?selectedYear=<YYYY>` 拿周报 PDF id → `GET /reports/GetPdfFile?Id=<id>` 下载归档周报，"SUMMARY - CUMULATIVE" 页的 ALL UPLAND COTTON 行即全国当周累计（outstanding/累计出口/总签约/出口预估）。当期全国数可下 `GET /reports/GetInterimReportFile?reportName=CWRCommoditySummary&format=.xlsx`（当周+上周全国全商品汇总）。
- 周报叙述文本：`GET /reports/WeeklyHighlightsData?WeekEndingDate=<yyyy-mm-dd>`。

**原始包缓存（`data/_tmp/`，可复用）**：`psd_alldata_csv.zip`（USDA 全商品 PSD，糖/谷物/油籽通用）、`cmo_monthly.xlsx`（Pink Sheet 全商品月度价）、`deacot2026.zip`（CFTC 年度包）。

**关键口径提醒**：
- 棉花市场年度 = **8 月–次年 7 月**
- 库消比分母 = Domestic Use（消费，不含出口），全球 vs 剥离中国两口径必须同时给（中国国储占全球库存约一半）
- PSD 每 (国别,年,属性) 只有最新修订值，无同期口径；WASDE 同期口径需另下月度快照 CSV
