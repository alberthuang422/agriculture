$ErrorActionPreference='Stop'
$root=Join-Path $PSScriptRoot '..'
$dataDir=Join-Path $root 'data\india_sugarcane_weather'
$daily=Import-Csv (Join-Path $dataDir 'india_major_sugarcane_regions_daily_1981_present.csv')
$result=foreach($sg in ($daily|Where-Object{$_.date -match '-09-(\d\d)$' -and [int]$Matches[1] -le 24}|Group-Object state)){
  $years=$sg.Group|Group-Object{$_.date.Substring(0,4)}
  $annual=foreach($yg in $years){
    $valid=@($yg.Group|Where-Object{$_.precip_mm_day -ne '-999.0'})
    if($valid.Count -ge 22){[pscustomobject]@{year=[int]$yg.Name;days=$valid.Count;rain=[double](($valid|Measure-Object precip_mm_day -Sum).Sum)}}
  }
  $base=@($annual|Where-Object{$_.year -ge 1991 -and $_.year -le 2020}|Sort-Object rain)
  $current=$annual|Where-Object{$_.year -eq 2026}
  $values=@($base|ForEach-Object{$_.rain})
  $mean=($values|Measure-Object -Average).Average
  $std=[math]::Sqrt((($values|ForEach-Object{[math]::Pow($_-$mean,2)}|Measure-Object -Sum).Sum)/($values.Count-1))
  $lower=@($values|Where-Object{$_ -lt $current.rain}).Count
  $equal=@($values|Where-Object{$_ -eq $current.rain}).Count
  $rank=100*($lower+0.5*$equal)/$values.Count
  $median=if($values.Count%2){$values[[int][math]::Floor($values.Count/2)]}else{($values[$values.Count/2-1]+$values[$values.Count/2])/2}
  $q10=$values[[int][math]::Floor(($values.Count-1)*0.1)]
  $q90=$values[[int][math]::Floor(($values.Count-1)*0.9)]
  $dry20=@($values|Where-Object{$_ -le $mean*0.8}).Count
  $dry40=@($values|Where-Object{$_ -le $mean*0.6}).Count
  [pscustomobject]@{state=$sg.Name;window_days=$current.days;rain_2026_mm=[math]::Round($current.rain,1);normal_mean_mm=[math]::Round($mean,1);normal_median_mm=[math]::Round($median,1);normal_sd_mm=[math]::Round($std,1);normal_p10_mm=[math]::Round($q10,1);normal_p90_mm=[math]::Round($q90,1);historical_percentile=[math]::Round($rank,0);years_n=$values.Count;years_atleast20pct_below_mean=$dry20;years_atleast40pct_below_mean=$dry40}
}
$path=Join-Path $dataDir 'september_rainfall_variability_1991_2020.csv'
$result|Sort-Object state|Export-Csv -LiteralPath $path -NoTypeInformation -Encoding utf8
Write-Output "Wrote distribution statistics to $path"
