#!/bin/bash
# ============================================================
# 编码检查脚本 - check-encoding.sh
# 功能：检查文件是否为UTF-8 without BOM编码
# 用法：./check-encoding.sh [目录路径] [文件扩展名]
# 示例：./check-encoding.sh ./src "py,js,ts,md"
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 默认配置
DEFAULT_DIR="."
DEFAULT_EXTENSIONS="py,js,ts,jsx,tsx,vue,go,java,kt,rs,md,json,yaml,yml,sh"

# 统计变量
total_files=0
passed_files=0
failed_files=0
bom_files=0
wrong_encoding_files=0

# 显示帮助信息
show_help() {
    echo "编码检查脚本 - 检查文件是否为UTF-8 without BOM编码"
    echo ""
    echo "用法："
    echo "  $0 [目录路径] [文件扩展名]"
    echo ""
    echo "参数："
    echo "  目录路径      要检查的目录路径（默认：当前目录）"
    echo "  文件扩展名    要检查的文件扩展名，逗号分隔（默认：常见源代码文件）"
    echo ""
    echo "选项："
    echo "  -h, --help    显示此帮助信息"
    echo "  -v, --verbose 显示详细输出"
    echo "  -q, --quiet   静默模式，只显示错误"
    echo ""
    echo "示例："
    echo "  $0                              # 检查当前目录所有源代码文件"
    echo "  $0 ./src                        # 检查src目录"
    echo "  $0 ./src 'py,js,ts'             # 只检查Python和JavaScript文件"
    echo "  $0 ./project 'md,txt'           # 只检查Markdown和文本文件"
    echo ""
    echo "退出码："
    echo "  0 - 所有文件检查通过"
    echo "  1 - 发现编码问题"
    echo "  2 - 参数错误"
}

# 检查文件是否包含BOM
check_bom() {
    local file="$1"
    # 读取文件前3字节
    local bom=$(head -c 3 "$file" 2>/dev/null | xxd -p)
    if [[ "$bom" == "efbbbf" ]]; then
        return 0  # 包含BOM
    fi
    return 1  # 不包含BOM
}

# 检查文件编码是否为UTF-8
check_encoding() {
    local file="$1"
    local encoding=$(file -b --mime-encoding "$file" 2>/dev/null)
    
    # UTF-8和US-ASCII（UTF-8的子集）都是可接受的
    if [[ "$encoding" == "utf-8" || "$encoding" == "us-ascii" ]]; then
        return 0
    fi
    return 1
}

# 检查行尾是否为LF
check_line_ending() {
    local file="$1"
    # 检查是否包含CRLF
    if grep -q $'\r' "$file" 2>/dev/null; then
        return 1  # 包含CRLF
    fi
    return 0  # 只有LF
}

# 检查单个文件
check_file() {
    local file="$1"
    local has_error=0
    local errors=""
    
    ((total_files++))
    
    # 检查编码
    if ! check_encoding "$file"; then
        local encoding=$(file -b --mime-encoding "$file" 2>/dev/null)
        errors="${errors}编码错误(检测到:$encoding); "
        ((wrong_encoding_files++))
        has_error=1
    fi
    
    # 检查BOM
    if check_bom "$file"; then
        errors="${errors}包含BOM; "
        ((bom_files++))
        has_error=1
    fi
    
    # 检查行尾
    if ! check_line_ending "$file"; then
        errors="${errors}行尾为CRLF(应为LF); "
        has_error=1
    fi
    
    if [[ $has_error -eq 0 ]]; then
        ((passed_files++))
        if [[ $verbose -eq 1 ]]; then
            echo -e "${GREEN}[通过]${NC} $file"
        fi
    else
        ((failed_files++))
        echo -e "${RED}[失败]${NC} $file - ${errors}"
    fi
    
    return $has_error
}

# 主检查函数
main_check() {
    local target_dir="$1"
    local extensions="$2"
    
    # 构建find命令的扩展名参数
    local find_args=""
    IFS=',' read -ra EXT_ARRAY <<< "$extensions"
    for ext in "${EXT_ARRAY[@]}"; do
        ext=$(echo "$ext" | tr -d ' ')
        if [[ -n "$find_args" ]]; then
            find_args="$find_args -o"
        fi
        find_args="$find_args -name \"*.$ext\""
    done
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}编码检查脚本${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "检查目录: $target_dir"
    echo "文件扩展名: $extensions"
    echo ""
    
    # 查找并检查文件
    eval "find \"$target_dir\" -type f \\( $find_args \\)" | while read -r file; do
        # 跳过.git等隐藏目录
        if [[ "$file" == *"/.git/"* ]]; then
            continue
        fi
        check_file "$file"
    done
    
    # 输出统计信息
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}检查结果统计${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "检查文件总数: $total_files"
    echo -e "通过: ${GREEN}$passed_files${NC}"
    echo -e "失败: ${RED}$failed_files${NC}"
    echo ""
    
    if [[ $bom_files -gt 0 ]]; then
        echo -e "${YELLOW}警告: 发现 $bom_files 个文件包含BOM${NC}"
    fi
    
    if [[ $wrong_encoding_files -gt 0 ]]; then
        echo -e "${YELLOW}警告: 发现 $wrong_encoding_files 个文件编码不正确${NC}"
    fi
    
    # 返回退出码
    if [[ $failed_files -gt 0 ]]; then
        return 1
    fi
    return 0
}

# 解析参数
verbose=0
quiet=0
target_dir="$DEFAULT_DIR"
extensions="$DEFAULT_EXTENSIONS"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            verbose=1
            shift
            ;;
        -q|--quiet)
            quiet=1
            shift
            ;;
        *)
            if [[ -z "$target_dir" || "$target_dir" == "$DEFAULT_DIR" ]]; then
                target_dir="$1"
            elif [[ -z "$extensions" || "$extensions" == "$DEFAULT_EXTENSIONS" ]]; then
                extensions="$1"
            fi
            shift
            ;;
    esac
done

# 验证目录
if [[ ! -d "$target_dir" ]]; then
    echo -e "${RED}错误: 目录不存在: $target_dir${NC}"
    exit 2
fi

# 执行检查
main_check "$target_dir" "$extensions"
exit $?
