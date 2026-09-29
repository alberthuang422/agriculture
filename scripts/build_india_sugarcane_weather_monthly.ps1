$ErrorActionPreference = 'Stop'
$dataDir = Join-Path $PSScriptRoot '..\data\india_sugarcane_weather'
$dailyPath = Join-Path $dataDir 'india_major_sugarcane_regions_daily_1981_present.csv'
$oniPath = Join-Path $PSScriptRoot '..\data\agri\raw\oni.txt'
$monthlyPath = Join-Path $dataDir 'india_major_sugarcane_regions_monthly_1981_present.csv'
$strongPath = Join-Path $dataDir 'india_major_sugarcane_regions_strong_elnino_years.csv'

# Strong recent ENSO episodes defined from the project NOAA ONI series.
$eventYears = @{
    1982='1982-83'; 1983='1982-83';
    1997='1997-98'; 1998='1997-98';
    2015='2015-16'; 2016='2015-16';
    2023='2023-24'; 2024='2023-24'
}
$oni = @{}
foreach ($line in Get-Content -LiteralPath $oniPath | Select-Object -Skip 1) {
    if ($line -match '^\s*(\w{3})\s+(\d{4})\s+[-\d.]+\s+([-\d.]+)') {
        $key = "$($Matches[2])-$($Matches[1])"
        $oni[$key] = [double]$Matches[3]
    }
}

$daily = Import-Csv -LiteralPath $dailyPath
$groups = $daily | Group-Object { '{0}|{1}|{2}' -f $_.state,$_.date.Substring(0,4),$_.date.Substring(5,2) }
$monthly = foreach ($g in $groups) {
    $sample = $g.Group[0]
    $year = [int]$sample.date.Substring(0,4)
    $month = [int]$sample.date.Substring(5,2)
    $ani = $null
    # ONI is a three-month running mean. Use its centered season (month name) where available.
    $seasonNames = @('DJF','JFM','FMA','MAM','AMJ','MJJ','JJA','JAS','ASO','SON','OND','NDJ')
    $season = $seasonNames[$month - 1]
    $oniKey = '{0}-{1}' -f $year,$season
    if ($oni.ContainsKey($oniKey)) { $ani = $oni[$oniKey] }
    $valid = @{}
    foreach ($field in @('tmax_c','tmin_c','precip_mm_day','solar_mj_m2_day','relative_humidity_pct')) {
        $vals = @($g.Group | ForEach-Object { [double]$_.$field } | Where-Object { $_ -ne -999 -and $_ -gt -900 })
        $valid[$field] = $vals
    }
    $rainTotal = if ($valid.precip_mm_day.Count -eq $g.Count) { ($valid.precip_mm_day | Measure-Object -Sum).Sum } else { $null }
    [pscustomobject]@{
        year = $year; month = $month; state = $sample.state
        representative_city = $sample.representative_city
        n_days = $g.Count
        tmax_valid_days = $valid.tmax_c.Count; tmin_valid_days = $valid.tmin_c.Count
        precip_valid_days = $valid.precip_mm_day.Count
        tmax_mean_c = if ($valid.tmax_c.Count) { [math]::Round(($valid.tmax_c | Measure-Object -Average).Average,2) } else { $null }
        tmin_mean_c = if ($valid.tmin_c.Count) { [math]::Round(($valid.tmin_c | Measure-Object -Average).Average,2) } else { $null }
        diurnal_temp_range_mean_c = if ($valid.tmax_c.Count -and $valid.tmin_c.Count) { [math]::Round((($valid.tmax_c | Measure-Object -Average).Average) - (($valid.tmin_c | Measure-Object -Average).Average),2) } else { $null }
        precip_total_mm = if ($null -ne $rainTotal) { [math]::Round($rainTotal,2) } else { $null }
        rain_days_ge_1mm = @($valid.precip_mm_day | Where-Object { $_ -ge 1 }).Count
        solar_mean_mj_m2_day = if ($valid.solar_mj_m2_day.Count) { [math]::Round(($valid.solar_mj_m2_day | Measure-Object -Average).Average,2) } else { $null }
        humidity_mean_pct = if ($valid.relative_humidity_pct.Count) { [math]::Round(($valid.relative_humidity_pct | Measure-Object -Average).Average,2) } else { $null }
        solar_valid_days = $valid.solar_mj_m2_day.Count
        humidity_valid_days = $valid.relative_humidity_pct.Count
        oni_season = $season; oni_c = $ani
        strong_elnino_event = if ($eventYears.ContainsKey($year)) { $eventYears[$year] } else { '' }
    }
}
$monthly | Sort-Object year,month,state | Export-Csv -LiteralPath $monthlyPath -NoTypeInformation -Encoding utf8
$monthly | Where-Object { $_.strong_elnino_event } | Sort-Object year,month,state | Export-Csv -LiteralPath $strongPath -NoTypeInformation -Encoding utf8
Write-Output "Monthly rows: $(@($monthly).Count); strong-event rows: $(@($monthly | Where-Object { $_.strong_elnino_event }).Count)"
