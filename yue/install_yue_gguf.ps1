# ============================================================
# YuE GGUF モデル 完全インストールスクリプト
# 統合版: 必要なアプリの確認・インストール + モデルダウンロード
# ============================================================

param(
    [string]$Quantization = "",
    [switch]$AutoInstall = $false,
    [switch]$SkipPython = $false
)

# 管理者権限チェック
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  YuE GGUF モデル 完全セットアップ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# ステップ1: システム要件の確認
# ============================================================
Write-Host "[ステップ1] システム要件を確認中..." -ForegroundColor Yellow
$totalRAM = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
$freeSpace = (Get-PSDrive C).Free / 1GB

Write-Host "  総RAM: $([math]::Round($totalRAM, 2)) GB" -ForegroundColor Cyan
Write-Host "  空きディスク容量: $([math]::Round($freeSpace, 2)) GB" -ForegroundColor Cyan
Write-Host ""

$warnings = @()
if ($totalRAM -lt 8) {
    $warnings += "RAMが8GB未満です。Q4_0量子化を推奨します。"
}
if ($freeSpace -lt 10) {
    $warnings += "空き容量が10GB未満です。モデル用の容量を確保してください。"
}

if ($warnings.Count -gt 0) {
    foreach ($warning in $warnings) {
        Write-Host "  警告: $warning" -ForegroundColor Yellow
    }
    Write-Host ""
}

# ============================================================
# ステップ2: Pythonの確認とインストール
# ============================================================
Write-Host "[ステップ2] Pythonを確認中..." -ForegroundColor Yellow
$pythonInstalled = $false
$pythonVersion = $null

# Pythonのパスを確認
$pythonPaths = @("python", "python3", "py")
foreach ($pythonCmd in $pythonPaths) {
    try {
        $versionOutput = & $pythonCmd --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonInstalled = $true
            $pythonVersion = $versionOutput
            Write-Host "  Pythonが見つかりました: $versionOutput" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonInstalled) {
    Write-Host "  Pythonが見つかりません。" -ForegroundColor Yellow
    
    if ($SkipPython) {
        Write-Host "  Pythonのインストールをスキップします。" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "  Pythonをインストールしますか？" -ForegroundColor Yellow
        Write-Host "  1. 自動インストール (winget使用)" -ForegroundColor White
        Write-Host "  2. 手動インストール (ブラウザでダウンロードページを開く)" -ForegroundColor White
        Write-Host "  3. スキップ (後で手動インストール)" -ForegroundColor White
        Write-Host ""
        
        if ($AutoInstall) {
            $pythonChoice = "1"
        } else {
            $pythonChoice = Read-Host "選択してください (1-3)"
        }
        
        switch ($pythonChoice) {
            "1" {
                Write-Host "  wingetでPythonをインストール中..." -ForegroundColor Green
                try {
                    winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
                    Write-Host "  Pythonのインストールが完了しました。" -ForegroundColor Green
                    Write-Host "  新しいPowerShellウィンドウを開いて再度実行してください。" -ForegroundColor Yellow
                    $pythonInstalled = $true
                } catch {
                    Write-Host "  wingetでのインストールに失敗しました。手動インストールを試してください。" -ForegroundColor Red
                    Start-Process "https://www.python.org/downloads/"
                }
            }
            "2" {
                Write-Host "  Pythonダウンロードページを開いています..." -ForegroundColor Green
                Start-Process "https://www.python.org/downloads/"
                Write-Host "  インストール後、このスクリプトを再実行してください。" -ForegroundColor Yellow
                exit 0
            }
            "3" {
                Write-Host "  Pythonのインストールをスキップします。" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host ""

# ============================================================
# ステップ3: GGUF Loaderの確認とインストール
# ============================================================
Write-Host "[ステップ3] GGUF Loaderを確認中..." -ForegroundColor Yellow

# GGUF Loaderの確認方法（複数の可能性をチェック）
$ggufLoaderInstalled = $false
$ggufLoaderPath = $null

# 方法1: コマンドラインから確認
$ggufCommands = @("ggufloader", "gguf-loader")
foreach ($cmd in $ggufCommands) {
    $cmdPath = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($cmdPath) {
        $ggufLoaderInstalled = $true
        $ggufLoaderPath = $cmdPath.Source
        Write-Host "  GGUF Loaderが見つかりました: $ggufLoaderPath" -ForegroundColor Green
        break
    }
}

# 方法2: 一般的なインストール場所を確認
if (-not $ggufLoaderInstalled) {
    $commonPaths = @(
        "$env:ProgramFiles\GGUF Loader",
        "$env:ProgramFiles(x86)\GGUF Loader",
        "$env:LOCALAPPDATA\Programs\GGUF Loader",
        "$env:USERPROFILE\AppData\Local\GGUF Loader"
    )
    
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            $exePath = Join-Path $path "GGUF Loader.exe"
            if (Test-Path $exePath) {
                $ggufLoaderInstalled = $true
                $ggufLoaderPath = $exePath
                Write-Host "  GGUF Loaderが見つかりました: $exePath" -ForegroundColor Green
                break
            }
        }
    }
}

# 方法3: Pythonパッケージとして確認
if (-not $ggufLoaderInstalled -and $pythonInstalled) {
    try {
        $pipCheck = & python -m pip show ggufloader 2>&1
        if ($LASTEXITCODE -eq 0) {
            $ggufLoaderInstalled = $true
            Write-Host "  GGUF Loader (Pythonパッケージ) が見つかりました" -ForegroundColor Green
        }
    } catch {
        # パッケージが見つからない
    }
}

if (-not $ggufLoaderInstalled) {
    Write-Host "  GGUF Loaderが見つかりません。" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  GGUF Loaderのインストール方法を選択してください:" -ForegroundColor Yellow
    Write-Host "  1. Pythonパッケージとしてインストール (pip install ggufloader)" -ForegroundColor White
    Write-Host "  2. スタンドアロンアプリをダウンロード (ブラウザで開く)" -ForegroundColor White
    Write-Host "  3. スキップ (後で手動インストール)" -ForegroundColor White
    Write-Host ""
    
    if ($AutoInstall) {
        $ggufChoice = "1"
    } else {
        $ggufChoice = Read-Host "選択してください (1-3)"
    }
    
    switch ($ggufChoice) {
        "1" {
            if ($pythonInstalled) {
                Write-Host "  pipでGGUF Loaderをインストール中..." -ForegroundColor Green
                try {
                    & python -m pip install ggufloader --upgrade
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "  GGUF Loaderのインストールが完了しました。" -ForegroundColor Green
                        $ggufLoaderInstalled = $true
                    } else {
                        Write-Host "  インストールに失敗しました。" -ForegroundColor Red
                    }
                } catch {
                    Write-Host "  エラー: $_" -ForegroundColor Red
                }
            } else {
                Write-Host "  Pythonがインストールされていないため、インストールできません。" -ForegroundColor Red
            }
        }
        "2" {
            Write-Host "  GGUF Loaderダウンロードページを開いています..." -ForegroundColor Green
            Start-Process "https://ggufloader.github.io/"
            Write-Host "  インストール後、このスクリプトを再実行してください。" -ForegroundColor Yellow
        }
        "3" {
            Write-Host "  GGUF Loaderのインストールをスキップします。" -ForegroundColor Yellow
        }
    }
}

Write-Host ""

# ============================================================
# ステップ4: ディレクトリ構造の作成
# ============================================================
$modelsDir = Join-Path $PSScriptRoot "Models\YuE"
Write-Host "[ステップ4] ディレクトリ構造を作成中..." -ForegroundColor Yellow
if (-not (Test-Path $modelsDir)) {
    New-Item -ItemType Directory -Path $modelsDir -Force | Out-Null
    Write-Host "  作成しました: $modelsDir" -ForegroundColor Green
} else {
    Write-Host "  ディレクトリは既に存在します: $modelsDir" -ForegroundColor Yellow
}
Write-Host ""

# ============================================================
# ステップ5: モデルダウンロード
# ============================================================
Write-Host "[ステップ5] モデルダウンロード" -ForegroundColor Yellow
Write-Host ""

# 量子化レベルの選択
if ([string]::IsNullOrEmpty($Quantization)) {
    Write-Host "量子化レベルを選択してください:" -ForegroundColor Yellow
    Write-Host "  1. Q4_0  - 低メモリ、高速 (8GB RAM推奨)" -ForegroundColor White
    Write-Host "  2. Q6_K  - バランス型 (16GB+ RAM推奨)" -ForegroundColor White
    Write-Host "  3. Q8_0  - 高精度、低速 (より多くのRAMが必要)" -ForegroundColor White
    Write-Host "  4. ダウンロードをスキップ" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "選択してください (1-4)"
    
    switch ($choice) {
        "1" { $quant = "Q4_0" }
        "2" { $quant = "Q6_K" }
        "3" { $quant = "Q8_0" }
        "4" { 
            Write-Host "ダウンロードをスキップします。" -ForegroundColor Yellow
            $quant = $null
        }
        default { 
            Write-Host "無効な選択です。Q6_Kをデフォルトとして使用します。" -ForegroundColor Yellow
            $quant = "Q6_K"
        }
    }
} else {
    $quant = $Quantization
}

if ($quant) {
    # モデル情報
    $baseUrl = "https://huggingface.co/Aryanne/YuE-s1-7B-anneal-en-cot-Q6_K-GGUF/resolve/main"
    $modelFiles = @{
        "Q4_0" = "yue-s1-7b-anneal-en-cot-q4_0.gguf"
        "Q6_K" = "yue-s1-7b-anneal-en-cot-q6_k.gguf"
        "Q8_0" = "yue-s1-7b-anneal-en-cot-q8_0.gguf"
    }
    
    if (-not $modelFiles.ContainsKey($quant)) {
        Write-Host "エラー: 無効な量子化レベルです。利用可能なオプション: Q4_0, Q6_K, Q8_0" -ForegroundColor Red
        exit 1
    }
    
    $fileName = $modelFiles[$quant]
    $filePath = Join-Path $modelsDir $fileName
    $downloadUrl = "$baseUrl/$fileName"
    
    Write-Host "量子化: $quant" -ForegroundColor Cyan
    Write-Host "モデルファイル: $fileName" -ForegroundColor Cyan
    Write-Host "保存先: $filePath" -ForegroundColor Cyan
    Write-Host ""
    
    # ファイルが既に存在するか確認
    if (Test-Path $filePath) {
        $fileSize = (Get-Item $filePath).Length / 1GB
        Write-Host "ファイルは既に存在します: $([math]::Round($fileSize, 2)) GB" -ForegroundColor Yellow
        $response = Read-Host "上書きしますか？ (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Host "ダウンロードをスキップします。" -ForegroundColor Yellow
        } else {
            Remove-Item $filePath -Force
        }
    }
    
    if (-not (Test-Path $filePath)) {
        Write-Host "ダウンロードを開始します..." -ForegroundColor Green
        Write-Host "注意: モデルファイルは大きいです (4-8GB)。時間がかかる場合があります。" -ForegroundColor Yellow
        Write-Host ""
        
        try {
            $ProgressPreference = 'Continue'
            Invoke-WebRequest -Uri $downloadUrl -OutFile $filePath -UseBasicParsing
            
            Write-Host ""
            Write-Host "ダウンロードが完了しました！" -ForegroundColor Green
            $fileSize = (Get-Item $filePath).Length / 1GB
            Write-Host "ファイルサイズ: $([math]::Round($fileSize, 2)) GB" -ForegroundColor Cyan
            Write-Host "保存先: $filePath" -ForegroundColor Green
            
        } catch {
            Write-Host ""
            Write-Host "ダウンロードエラー: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "代替ダウンロード方法:" -ForegroundColor Yellow
            Write-Host "1. 訪問: https://huggingface.co/Aryanne/YuE-s1-7B-anneal-en-cot-Q6_K-GGUF" -ForegroundColor White
            Write-Host "2. 'Files and versions'タブをクリック" -ForegroundColor White
            Write-Host "3. $fileName ファイルを手動でダウンロード" -ForegroundColor White
        }
    }
}

Write-Host ""

# ============================================================
# 完了メッセージ
# ============================================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  セットアップ完了！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "次のステップ:" -ForegroundColor Yellow
Write-Host ""

if (-not $ggufLoaderInstalled) {
    Write-Host "1. GGUF Loaderをインストールしてください:" -ForegroundColor White
    Write-Host "   - Pythonパッケージ: pip install ggufloader" -ForegroundColor Cyan
    Write-Host "   - または: https://ggufloader.github.io/" -ForegroundColor Cyan
    Write-Host ""
}

if ($quant -and (Test-Path $filePath)) {
    Write-Host "2. GGUF Loaderでモデルを読み込んでください:" -ForegroundColor White
    Write-Host "   モデルパス: $filePath" -ForegroundColor Cyan
    Write-Host ""
    
    # GGUF Loaderがインストールされている場合、起動を試みる
    if ($ggufLoaderInstalled) {
        Write-Host "3. GGUF Loaderを起動しますか？ (y/N)" -ForegroundColor Yellow
        $launch = Read-Host
        if ($launch -eq "y" -or $launch -eq "Y") {
            if ($ggufLoaderPath) {
                Start-Process $ggufLoaderPath
            } elseif ($pythonInstalled) {
                Write-Host "   ggufloaderコマンドで起動してください" -ForegroundColor Yellow
            }
        }
    }
} else {
    Write-Host "2. モデルファイルをダウンロードしてください" -ForegroundColor White
    Write-Host ""
}

Write-Host "3. ローカルAIモデルとのチャットを開始してください！" -ForegroundColor White
Write-Host ""

