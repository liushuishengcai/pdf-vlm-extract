@echo off
chcp 65001 >nul
REM PDF VLM Extract - Hermes Skill 安装脚本（Windows）

setlocal enabledelayedexpansion

set "SKILL_DIR=%USERPROFILE%\AppData\Local\hermes\skills\system\pdf-vlm-extract"

echo 安装到: %SKILL_DIR%

REM 创建目录
if not exist "%SKILL_DIR%\scripts" (
    mkdir "%SKILL_DIR%\scripts"
)

REM 复制文件
copy /y "SKILL.md" "%SKILL_DIR%\" >nul
if errorlevel 1 (
    echo ❌ 复制 SKILL.md 失败
    exit /b 1
)

copy /y "scripts\pdf_vlm_extract.py" "%SKILL_DIR%\scripts\" >nul
if errorlevel 1 (
    echo ❌ 复制脚本失败
    exit /b 1
)

REM 验证
if exist "%SKILL_DIR%\SKILL.md" (
    if exist "%SKILL_DIR%\scripts\pdf_vlm_extract.py" (
        echo ✅ Skill 安装成功！
        echo.
        echo 使用方法：
        echo   1. 确保已设置环境变量 HERMES_CUSTOM_ALI_API_KEY
        echo   2. 在 Hermes 中说：提取这个 PDF
        echo.
        echo 或手动运行：
        echo   python "%SKILL_DIR%\scripts\pdf_vlm_extract.py" book.pdf
        exit /b 0
    )
)

echo ❌ 安装失败
exit /b 1
