Set-Location C:\Users\S\sct-agency-bots
$agents = Get-ChildItem -Path agents -Filter *.py -Recurse
$bots = Get-ChildItem -Path bots -Filter *.py -Recurse
$wf = Get-ChildItem -Path '.github\workflows' -Filter *.yml
$pages = Get-ChildItem -Path site -Filter *.html -Recurse
$funcs = Get-ChildItem -Path 'netlify\functions' -Filter *.js -Recurse
Write-Host "=== SYSTEM INVENTORY ==="
Write-Host ("AGENTS: " + $agents.Count)
Write-Host ("BOTS: " + $bots.Count)
Write-Host ("WORKFLOWS: " + $wf.Count)
Write-Host ("SITE PAGES: " + $pages.Count)
Write-Host ("NETLIFY FUNCS: " + $funcs.Count)
$totalAgentKB = 0
Write-Host "`n=== AGENT FILES BY SIZE ==="
foreach($a in ($agents | Sort-Object Length -Descending)) {
    $kb = [math]::Round($a.Length/1024,1)
    $totalAgentKB += $kb
    $rel = $a.FullName.Replace('C:\Users\S\sct-agency-bots\','')
    Write-Host "$rel : ${kb}KB"
}
Write-Host ("`nTOTAL AGENT CODE: " + [math]::Round($totalAgentKB,0) + "KB")
Write-Host "`n=== WORKFLOW FILES ==="
foreach($w in ($wf | Sort-Object Name)) { Write-Host $w.Name }
Write-Host ("`n=== BOT COUNT BY PREFIX ===")
$bots | ForEach-Object { $_.Name.Split('_')[0] } | Group-Object | Sort-Object Count -Descending | Select-Object -First 20 | ForEach-Object { Write-Host ($_.Name + ": " + $_.Count) }
