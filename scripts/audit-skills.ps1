param(
    [string]$SkillRoot = ".agents/skills"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path ".").Path
$rootPath = Join-Path $repoRoot $SkillRoot

if (-not (Test-Path -LiteralPath $rootPath)) {
    throw "Skill root not found: $SkillRoot"
}

$skillFiles = Get-ChildItem -LiteralPath $rootPath -Recurse -Filter "SKILL.md" -File

if ($skillFiles.Count -eq 0) {
    throw "No SKILL.md files found under $SkillRoot"
}

$errors = New-Object System.Collections.Generic.List[string]

foreach ($file in $skillFiles) {
    $relativePath = Resolve-Path -LiteralPath $file.FullName -Relative
    $lines = Get-Content -LiteralPath $file.FullName

    if ($lines.Count -lt 4) {
        $errors.Add("${relativePath}: file is too short to contain valid frontmatter")
        continue
    }

    if ($lines[0] -ne "---") {
        $errors.Add("${relativePath}: missing opening frontmatter delimiter")
    }

    $closingIndex = -1
    for ($i = 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -eq "---") {
            $closingIndex = $i
            break
        }
    }

    if ($closingIndex -lt 0) {
        $errors.Add("${relativePath}: missing closing frontmatter delimiter")
        continue
    }

    $frontmatter = $lines[1..($closingIndex - 1)]

    if (-not ($frontmatter | Where-Object { $_ -match '^name:\s+\S+' })) {
        $errors.Add("${relativePath}: missing non-empty name frontmatter")
    }

    if (-not ($frontmatter | Where-Object { $_ -match '^description:\s+\S+' })) {
        $errors.Add("${relativePath}: missing non-empty description frontmatter")
    }

    if (-not ($lines | Where-Object { $_ -match '^#\s+\S+' })) {
        $errors.Add("${relativePath}: missing top-level heading")
    }

    $fenceCount = ($lines | Where-Object { $_ -match '^```' }).Count
    if (($fenceCount % 2) -ne 0) {
        $errors.Add("${relativePath}: unbalanced Markdown code fences")
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    throw "Skill audit failed with $($errors.Count) issue(s)."
}

Write-Output "Skill audit passed for $($skillFiles.Count) file(s)."
