$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot '..'
$dataDir = Join-Path $root 'data\india_sugarcane_weather'
$monthly = Import-Csv (Join-Path $dataDir 'india_major_sugarcane_regions_monthly_1981_present.csv')
$states = @('Uttar Pradesh','Maharashtra','Karnataka','Tamil Nadu','Gujarat','Bihar','Andhra Pradesh','Telangana','Haryana')
$output = foreach ($actual in $monthly | Where-Object {
    $y=[int]$_.year; $m=[int]$_.month
    ($y -eq 2025 -and $m -ge 10) -or ($y -eq 2026 -and $m -le 5)
}) {
    $state=$actual.state; $month=[int]$actual.month; $year=[int]$actual.year
    $base=@($monthly | Where-Object {$_.state -eq $state -and [int]$_.month -eq $month -and [int]$_.year -ge 1991 -and [int]$_.year -le 2020})
    $norm=@{}
    foreach($f in @('tmax_mean_c','tmin_mean_c','diurnal_temp_range_mean_c','precip_total_mm','solar_mean_mj_m2_day','humidity_mean_pct')) {
        $v=@($base | ForEach-Object {if($_.$f -ne '') {[double]$_.$f}})
        $norm[$f]=if($v.Count){[double](($v|Measure-Object -Average).Average)}else{$null}
    }
    $solarActual=if($actual.solar_mean_mj_m2_day -ne ''){[double]$actual.solar_mean_mj_m2_day}else{$null}
    $rainActual=if($actual.precip_total_mm -ne ''){[double]$actual.precip_total_mm}else{$null}
    [pscustomobject]@{
        year=$year; month=$month; state=$state; representative_city=$actual.representative_city
        days=$actual.n_days; tmax_actual_c=[double]$actual.tmax_mean_c; tmax_normal_c=[math]::Round($norm.tmax_mean_c,2); tmax_anomaly_c=[math]::Round(([double]$actual.tmax_mean_c)-$norm.tmax_mean_c,2)
        tmin_actual_c=[double]$actual.tmin_mean_c; tmin_normal_c=[math]::Round($norm.tmin_mean_c,2); tmin_anomaly_c=[math]::Round(([double]$actual.tmin_mean_c)-$norm.tmin_mean_c,2)
        dtr_actual_c=[double]$actual.diurnal_temp_range_mean_c; dtr_normal_c=[math]::Round($norm.diurnal_temp_range_mean_c,2); dtr_anomaly_c=[math]::Round(([double]$actual.diurnal_temp_range_mean_c)-$norm.diurnal_temp_range_mean_c,2)
        rain_actual_mm=$rainActual; rain_normal_mm=[math]::Round($norm.precip_total_mm,1); rain_anomaly_pct=if($null -ne $rainActual -and $norm.precip_total_mm -gt 0){[math]::Round(100*($rainActual/$norm.precip_total_mm-1),0)}else{$null}
        solar_actual_mj=$solarActual; solar_normal_mj=if($null -ne $norm.solar_mean_mj_m2_day){[math]::Round($norm.solar_mean_mj_m2_day,2)}else{$null}; solar_anomaly_pct=if($null -ne $solarActual -and $norm.solar_mean_mj_m2_day -gt 0){[math]::Round(100*($solarActual/$norm.solar_mean_mj_m2_day-1),0)}else{$null}
        solar_valid_days=$actual.solar_valid_days; humidity_actual_pct=[double]$actual.humidity_mean_pct; humidity_normal_pct=[math]::Round($norm.humidity_mean_pct,1); oni_c=$actual.oni_c
    }
}
$outPath=Join-Path $dataDir 'weather_anomalies_oct2025_may2026_vs_1991_2020.csv'
$output | Sort-Object year,month,state | Export-Csv -LiteralPath $outPath -NoTypeInformation -Encoding utf8
Write-Output "Wrote $(@($output).Count) monthly comparisons to $outPath"
