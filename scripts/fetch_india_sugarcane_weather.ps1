$ErrorActionPreference = 'Stop'
$outDir = Join-Path $PSScriptRoot '..\data\india_sugarcane_weather'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$sites = @(
    @{state='Uttar Pradesh'; city='Lucknow'; lon=80.9462; lat=26.8467},
    @{state='Maharashtra'; city='Pune'; lon=73.8567; lat=18.5204},
    @{state='Karnataka'; city='Belagavi'; lon=74.5089; lat=15.8497},
    @{state='Tamil Nadu'; city='Coimbatore'; lon=76.9558; lat=11.0168},
    @{state='Gujarat'; city='Ahmedabad'; lon=72.5714; lat=23.0225},
    @{state='Bihar'; city='Patna'; lon=85.1376; lat=25.5941},
    @{state='Andhra Pradesh'; city='Vijayawada'; lon=80.6480; lat=16.5062},
    @{state='Telangana'; city='Nizamabad'; lon=78.0941; lat=18.6725},
    @{state='Haryana'; city='Karnal'; lon=76.9905; lat=29.6857}
)
$start = '19810101'
$end = (Get-Date).ToUniversalTime().ToString('yyyyMMdd')
$parameters = 'T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M'
$rows = [System.Collections.Generic.List[object]]::new()
$siteMetadata = [System.Collections.Generic.List[object]]::new()
foreach ($site in $sites) {
    $query = "parameters=$parameters&community=AG&longitude=$($site.lon)&latitude=$($site.lat)&start=$start&end=$end&format=JSON"
    $uri = "https://power.larc.nasa.gov/api/temporal/daily/point?$query"
    $data = Invoke-RestMethod -Uri $uri -TimeoutSec 180
    $weather = $data.properties.parameter
    $siteRowCount = 0
    foreach ($dayProperty in $weather.T2M_MAX.PSObject.Properties) {
        $day = $dayProperty.Name
        $rows.Add([pscustomobject]@{
            date = ('{0}-{1}-{2}' -f $day.Substring(0,4),$day.Substring(4,2),$day.Substring(6,2))
            state = $site.state; representative_city = $site.city
            latitude = $site.lat; longitude = $site.lon
            tmax_c = $weather.T2M_MAX.PSObject.Properties[$day].Value
            tmin_c = $weather.T2M_MIN.PSObject.Properties[$day].Value
            precip_mm_day = $weather.PRECTOTCORR.PSObject.Properties[$day].Value
            solar_mj_m2_day = $weather.ALLSKY_SFC_SW_DWN.PSObject.Properties[$day].Value
            relative_humidity_pct = $weather.RH2M.PSObject.Properties[$day].Value
        })
        $siteRowCount++
    }
    $siteMetadata.Add([pscustomobject]@{
        state = $site.state; city = $site.city; latitude = $site.lat; longitude = $site.lon
        api_header = $data.header; parameters = $data.parameters
    })
    Write-Output "$($site.state): $siteRowCount daily rows"
    Start-Sleep -Seconds 1
}
$csvPath = Join-Path $outDir 'india_major_sugarcane_regions_daily_1981_present.csv'
$rows | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding utf8
$metadata = [pscustomobject]@{
    source = 'NASA POWER Daily API'
    api = 'https://power.larc.nasa.gov/api/temporal/daily/point'
    retrieved_utc_date = $end; start = $start; end = $end
    parameters = @('T2M_MAX','T2M_MIN','PRECTOTCORR','ALLSKY_SFC_SW_DWN','RH2M')
    sites = @($siteMetadata)
    notes = @(
        'Each location is a representative point/grid cell, not a state-wide average.',
        'NASA POWER daily values are gridded/reanalysis/satellite-derived products; source metadata is included per site.',
        'NASA POWER missing/fill values (-999) are retained as returned.'
    )
}
$metadata | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $outDir 'source_metadata.json') -Encoding utf8
Write-Output "Wrote $($rows.Count) rows to $csvPath"
