$src = "src"
$tmp = "extract_tmp\src"
$diffs = @()

foreach ($file in (Get-ChildItem -Path $tmp -Recurse -File)) {
    $relPath = $file.FullName.Substring((Resolve-Path $tmp).Path.Length + 1)
    $srcPath = Join-Path $src $relPath
    
    if (-not (Test-Path $srcPath)) {
        $diffs += "NEW: $relPath"
    } else {
        $tmpContent = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        $srcContent = Get-Content $srcPath -Raw -ErrorAction SilentlyContinue
        if ($tmpContent -ne $srcContent) {
            # Check if it's just CRLF difference
            if (($tmpContent -replace "`r", "") -ne ($srcContent -replace "`r", "")) {
                $diffs += "MODIFIED: $relPath"
            }
        }
    }
}
$diffs | Out-File diffs.txt -Encoding utf8
