$ErrorActionPreference='Stop'
$root=Join-Path $PSScriptRoot '..'
$dataDir=Join-Path $root 'data\india_sugarcane_weather'
$daily=Import-Csv (Join-Path $dataDir 'india_major_sugarcane_regions_daily_1981_present.csv')
$results=foreach($stateGroup in ($daily|Where-Object{$_.date -match '-09-(\d\d)$' -and [int]$Matches[1] -le 24}|Group-Object state)) {
    $all=@($stateGroup.Group)
    $actual=@($all|Where-Object{$_.date -like '2026-09-*' -and $_.tmax_c -ne '-999.0' -and $_.precip_mm_day -ne '-999.0'})
    $historic=@($all|Where-Object{[int]$_.date.Substring(0,4) -ge 1991 -and [int]$_.date.Substring(0,4) -le 2020})
    $yearGroups=$historic|Group-Object{$_.date.Substring(0,4)}
    $histYear=foreach($yg in $yearGroups){
        $r=@($yg.Group|Where-Object{$_.tmax_c -ne '-999.0' -and $_.precip_mm_day -ne '-999.0'})
        [pscustomobject]@{rain=($r|Measure-Object -Property precip_mm_day -Sum).Sum;tmax=($r|Measure-Object -Property tmax_c -Average).Average;tmin=($r|Measure-Object -Property tmin_c -Average).Average;dtr=(@($r|ForEach-Object{[double]$_.tmax_c-[double]$_.tmin_c})|Measure-Object -Average).Average}
    }
    $rainNow=($actual|Measure-Object -Property precip_mm_day -Sum).Sum
    $tmaxNow=($actual|Measure-Object -Property tmax_c -Average).Average
    $tminNow=($actual|Measure-Object -Property tmin_c -Average).Average
    $dtrNow=(@($actual|ForEach-Object{[double]$_.tmax_c-[double]$_.tmin_c})|Measure-Object -Average).Average
    $rainNorm=($histYear|Measure-Object -Property rain -Average).Average
    $tmaxNorm=($histYear|Measure-Object -Property tmax -Average).Average
    $tminNorm=($histYear|Measure-Object -Property tmin -Average).Average
    $dtrNorm=($histYear|Measure-Object -Property dtr -Average).Average
    [pscustomobject]@{state=$stateGroup.Name;point_days=$actual.Count;rain_2026_mm=[math]::Round($rainNow,1);rain_1991_2020_mm=[math]::Round($rainNorm,1);rain_departure_pct=[math]::Round(100*($rainNow/$rainNorm-1),0);tmax_2026_c=[math]::Round($tmaxNow,2);tmax_1991_2020_c=[math]::Round($tmaxNorm,2);tmax_anomaly_c=[math]::Round($tmaxNow-$tmaxNorm,2);tmin_2026_c=[math]::Round($tminNow,2);tmin_1991_2020_c=[math]::Round($tminNorm,2);tmin_anomaly_c=[math]::Round($tminNow-$tminNorm,2);dtr_anomaly_c=[math]::Round($dtrNow-$dtrNorm,2)}
}
$out=Join-Path $dataDir 'weather_september_2026_vs_1991_2020.csv'
$results|Sort-Object state|Export-Csv -LiteralPath $out -NoTypeInformation -Encoding utf8
Write-Output "Wrote $(@($results).Count) same-window comparisons ($out)"
