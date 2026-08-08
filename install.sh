#!/bin/bash
# PDF VLM Extract - Hermes Skill 安装脚本（Linux/Mac）

set -e

SKILL_DIR="$HOME/.local/share/hermes/skills/system/pdf-vlm-extract"
SKILL_DIR_ALT="$HOME/AppData/Local/hermes/skills/system/pdf-vlm-extract"

# 检测 Hermes 安装位置
if [ -d "$HOME/AppData/Local/hermes" ]; then
    TARGET="$SKILL_DIR_ALT"
elif [ -d "$HOME/.local/share/hermes" ]; then
    TARGET="$SKILL_DIR"
else
    echo "未检测到 Hermes 安装，请选择安装目录："
    echo "1) $SKILL_DIR (标准 Linux)"
    echo "2) $SKILL_DIR_ALT (WSL/自定义)"
    echo "3) 自定义路径"
    read -p "选择 [1-3]: " choice
    
    case $choice in
        1) TARGET="$SKILL_DIR" ;;
        2) TARGET="$SKILL_DIR_ALT" ;;
        3) read -p "输入路径: " TARGET ;;
        *) echo "无效选择"; exit 1 ;;
    esac
fi

echo "安装到: $TARGET"

# 创建目录
mkdir -p "$TARGET/scripts"

# 复制文件
cp SKILL.md "$TARGET/"
cp scripts/pdf_vlm_extract.py "$TARGET/scripts/"

# 验证
if [ -f "$TARGET/SKILL.md" ] && [ -f "$TARGET/scripts/pdf_vlm_extract.py" ]; then
    echo "✅ Skill 安装成功！"
    echo ""
    echo "使用方法："
    echo "  1. 确保已设置环境变量 HERMES_CUSTOM_ALI_API_KEY"
    echo "  2. 在 Hermes 中说：提取这个 PDF"
    echo ""
    echo "或手动运行："
    echo "  python $TARGET/scripts/pdf_vlm_extract.py book.pdf"
else
    echo "❌ 安装失败"
    exit 1
fi
