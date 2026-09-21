param([ValidateSet("database","backend","frontend","stop-database")][string]$Target="backend")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$taskNode = Get-Command node -ErrorAction SilentlyContinue
$taskPg = Join-Path $PSScriptRoot ".tools/postgresql17/pgsql/bin"
$bundledPgReady = Join-Path $taskPg "pg_isready.exe"
$bundledPgControl = Join-Path $taskPg "pg_ctl.exe"
$systemPgReady = Get-Command pg_isready -ErrorAction SilentlyContinue
$pgReady = if (Test-Path -LiteralPath $bundledPgReady) { $bundledPgReady } elseif ($systemPgReady) { $systemPgReady.Source } else { $null }
switch ($Target) {
  "database" {
    if (!$pgReady) { throw "PostgreSQL не найден. Установите PostgreSQL 17 и добавьте его bin-каталог в PATH." }
    & $pgReady -h 127.0.0.1 -p 5432 -q
    if ($LASTEXITCODE -eq 0) {
      Write-Host "PostgreSQL уже работает на 127.0.0.1:5432. Можно запускать backend."
    } elseif (Test-Path -LiteralPath $bundledPgControl) {
      $taskPgLog = Join-Path $PSScriptRoot (".pgdata/server-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
      & $bundledPgControl -D .pgdata -l $taskPgLog -o "-p 5432 -h 127.0.0.1" -w start
      if ($LASTEXITCODE -ne 0) { throw "Не удалось запустить PostgreSQL. Проверьте журнал: $taskPgLog" }
    } else {
      throw "PostgreSQL установлен, но сервер не отвечает на 127.0.0.1:5432. Запустите службу PostgreSQL."
    }
  }
  "stop-database" {
    if (!(Test-Path -LiteralPath $bundledPgControl)) { throw "Остановка доступна только для переносной PostgreSQL из каталога .tools." }
    & $bundledPgControl -D .pgdata -m fast -w stop
  }
  "backend" {
    if (!(Test-Path -LiteralPath ".venv/Scripts/python.exe")) { throw "Виртуальное окружение не найдено. Выполните команды установки из README.md." }
    & .venv/Scripts/python.exe backend/manage.py runserver 127.0.0.1:8000
  }
  "frontend" {
    if (!$taskNode) { throw "Node.js не найден. Установите Node.js и откройте новый терминал." }
    if (!(Test-Path -LiteralPath "frontend/node_modules")) { throw "Зависимости frontend не установлены. Выполните: cd frontend; npm ci" }
    Set-Location frontend
    & $taskNode.Source node_modules/vite/bin/vite.js
  }
}
