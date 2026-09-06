$rootPath = "C:\_Рабочая_папка\Проекты_программирование\tg_digest\finance\Финансы_видео"
$logFile  = "C:\_Рабочая_папка\Проекты_программирование\tg_digest\finance\compress_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$exts     = @("*.mp4","*.avi","*.mov","*.mkv","*.wmv","*.flv","*.webm","*.m4v")

# Исключаем папку Никулиной — уже сжата ранее
$files = Get-ChildItem -Path $rootPath -Recurse -Include $exts |
         Where-Object { $_.FullName -notlike "*Никулиной*" -and $_.Name -notlike "__temp_*" }

$total = $files.Count; $i = 0; $totalSavedBytes = 0; $failedFiles = @()

function Log($msg) { Write-Host $msg; Add-Content -Path $logFile -Value $msg -Encoding UTF8 }

Log "========================================="
Log "Start: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Log "Files to compress: $total"
Log "Root: $rootPath"
Log "========================================="

foreach ($file in $files) {
    $i++
    $origSize   = $file.Length
    $origSizeMB = [math]::Round($origSize / 1MB, 1)
    $tempPath   = [IO.Path]::Combine($file.DirectoryName, "__temp_$($file.Name)")
    Log ""
    Log "[$i/$total] $($file.Name)  ($origSizeMB MB)"
    if (Test-Path $tempPath) { [System.IO.File]::Delete($tempPath) }
    & ffmpeg -nostats -loglevel error -i "$($file.FullName)" -filter_complex "[0:v]setpts=PTS/1.5[v];[0:a]atempo=1.5[a]" -map "[v]" -map "[a]" -c:v libx265 -crf 28 -preset fast -y "$tempPath"
    $exitCode = $LASTEXITCODE
    $tempExists = Test-Path $tempPath
    $tempSize = if ($tempExists) { (Get-Item $tempPath).Length } else { 0 }
    if ($exitCode -ne 0 -or -not $tempExists -or $tempSize -lt 1MB) {
        Log "  ERROR (exit=$exitCode) - original kept"
        if (Test-Path $tempPath) { [System.IO.File]::Delete($tempPath) }
        $failedFiles += $file.FullName
        continue
    }
    $newSizeMB = [math]::Round($tempSize / 1MB, 1)
    $savedMB   = [math]::Round(($origSize - $tempSize) / 1MB, 1)
    $totalSavedBytes += ($origSize - $tempSize)
    Log "  -> $newSizeMB MB  (saved $savedMB MB)"
    [System.IO.File]::Delete($file.FullName)
    Rename-Item -Path $tempPath -NewName $file.Name
    Log "  OK"
}

$totalSavedMB = [math]::Round($totalSavedBytes / 1MB, 0)
$totalSavedGB = [math]::Round($totalSavedBytes / 1GB, 2)
Log ""
Log "========================================="
Log "Finish: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Log "Done: $($total - $failedFiles.Count) / $total"
Log "Saved: $totalSavedMB MB  ($totalSavedGB GB)"
if ($failedFiles.Count -gt 0) { Log "Failed:"; foreach ($f in $failedFiles) { Log "  - $f" } }
Log "========================================="
