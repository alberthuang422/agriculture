# 印度主要甘蔗产区天气数据

## 已收集的数据

- `india_major_sugarcane_regions_daily_1981_present.csv`：1981-01-01 至 2026-09-27，9个甘蔗主产邦的逐日天气，约15万条地区-日期记录。
- `india_major_sugarcane_regions_monthly_1981_present.csv`：按邦和年月汇总的月度数据，并附 NOAA ONI 三个月滑动指数。
- `india_major_sugarcane_regions_strong_elnino_years.csv`：提取强厄尔尼诺事件覆盖年份，便于对比。
- `source_metadata.json`：NASA POWER 接口、站点坐标、单位及响应元数据。

主要覆盖北方邦、马哈拉施特拉邦、卡纳塔克邦、泰米尔纳德邦、古吉拉特邦、比哈尔邦、安得拉邦、特伦甘纳邦和哈里亚纳邦。每个邦目前用一个代表城市附近的 NASA POWER 网格点表示；这不是邦级面积加权平均，也不等于甘蔗种植区实测站点。

## 字段

| 字段 | 单位 | 说明 |
|---|---:|---|
| `tmax_c`, `tmin_c` | °C | 2米日最高/最低气温 |
| `precip_mm_day` | mm/日 | 校正降水量 |
| `solar_mj_m2_day` | MJ/m²/日 | 全天空地表短波辐射，作为日照/太阳能量代理 |
| `relative_humidity_pct` | % | 2米相对湿度 |
| `diurnal_temp_range_mean_c` | °C | 月平均最高温减月平均最低温 |
| `oni_c` | °C | NOAA ONI 三个月季节滑动海温距平；季节名称见 `oni_season` |
| `strong_elnino_event` | — | 按事件跨越的日历年标注：1982-83、1997-98、2015-16、2023-24 |

日度文件保留 NASA POWER 的 `-999` 缺测码。月表把缺测值排除在均值之外；`*_valid_days` 显示每项实际有效天数，降雨月总量在当月存在缺测时留空，避免把不完整月份误读为完整月累计。此批太阳辐射记录从1984-01-01起有值，且各变量最新有效日期不同（本次抓取至2026-09-27，但多数变量最新有效日约为2026-09-24）；使用时请检查 `solar_valid_days` 及其他有效天数列。

## 范围和限制

NASA POWER 提供长期格点/再分析及卫星融合气象估计，适合历史气候比较；不是印度气象局逐站原始观测。数据按代表点取值，不能直接推断全邦甘蔗产量或蔗糖率。分析糖分积累时，应按各地种植批次和成熟/收获窗口切片，重点比较成熟前约2-4个月的温度、夜温、昼夜温差、降雨/雨日、太阳辐射与湿度；还应尽可能加入灌溉、品种、收获日期和甘蔗品质数据。

强厄尔尼诺年份只是用于对比筛选，不代表印度每个邦都会出现同方向或同幅度的降雨/温度变化。厄尔尼诺影响需要按邦和季节独立估计。当前 ONI 原始序列来自项目内 `data/agri/raw/oni.txt`，该文件最新记录截至 2026 年 MJJ；2026/27 事件尚不能仅凭有限季节数据归为完整强事件，因此没有放进强事件筛选表。

## 来源

- NASA POWER Daily API: <https://power.larc.nasa.gov/docs/services/api/temporal/daily/>；参数含义和单位随 NASA 响应记录在 `source_metadata.json`。
- NOAA CPC ONI: <https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v5/>。
- 印度气象局 IMD 提供1901年以来的日降雨格点数据，可用于把降雨历史延长至1981年之前；但与这里的逐日多变量 NASA 数据来源和空间分辨率不同，后续合并时应保留来源标记。<https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_1_NetCDF.html>

## 重建

- `scripts/fetch_india_sugarcane_weather.ps1`：重新抓取 NASA POWER 日度数据。
- `scripts/build_india_sugarcane_weather_monthly.ps1`：从日度文件和项目 ONI 文件重建月度、强厄尔尼诺筛选表。
