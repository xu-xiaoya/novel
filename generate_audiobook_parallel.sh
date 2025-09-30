#!/bin/bash

# 有声书生成脚本 - 并行处理版本
# 使用云希声音生成第一卷有声书

NOVEL_DIR="/Users/xiaoyu/逆天仙途：因果投资万倍返还！"
VOLUME_DIR="$NOVEL_DIR/第一卷 青阳崛起"
OUTPUT_DIR="$NOVEL_DIR/有声书/第一卷_青阳崛起"
TTS_URL="http://192.168.31.252:5000"
VOICE="zh-CN-YunxiNeural"
MAX_JOBS=5  # 同时处理的最大任务数

echo "🎙️  开始生成《逆天仙途：因果投资万倍返还！》有声书"
echo "   使用声音: $VOICE (云希)"
echo "   并行任务数: $MAX_JOBS"
echo "   源目录: $VOLUME_DIR"
echo "   输出目录: $OUTPUT_DIR"
echo "$(printf '%*s' 50 '' | tr ' ' '-')"

# 确保输出目录存在
mkdir -p "$OUTPUT_DIR"

# 定义处理单个章节的函数
process_chapter() {
    local chapter_file="$1"
    local chapter_name="${chapter_file%.txt}"
    
    echo "🎧 [并行] 处理章节: $chapter_file"
    
    # 读取文件内容，清理格式
    local content=$(cat "$VOLUME_DIR/$chapter_file" | sed 's/^[[:space:]]*[0-9]*→//g' | tr -d '\r' | sed '/^[[:space:]]*$/d' | tr '\n' ' ')
    
    if [ -z "$content" ]; then
        echo "   ✗ [$chapter_file] 章节内容为空，跳过"
        return 1
    fi
    
    # 清理文本，转义双引号和特殊字符
    local clean_text=$(echo "$content" | sed 's/"/\\"/g' | sed 's/\\/\\\\/g')
    
    # 构建输出文件名
    local audio_file="$OUTPUT_DIR/${chapter_name}.mp3"
    
    echo "   🎵 [$chapter_file] 生成音频: $(basename "$audio_file")"
    
    # 构建JSON请求
    local json_data="{\"text\":\"$clean_text\",\"voice\":\"$VOICE\",\"file_name\":\"$(basename "$audio_file")\"}"
    
    # 调用TTS服务
    local curl_result=$(curl -s -X POST "$TTS_URL/tts" \
        -H "Content-Type: application/json" \
        -d "$json_data" \
        -o "$audio_file" \
        -w "%{http_code}")
    
    if [ "$curl_result" = "200" ] && [ -s "$audio_file" ]; then
        local file_size=$(stat -f%z "$audio_file" 2>/dev/null || stat -c%s "$audio_file" 2>/dev/null)
        if [ "$file_size" -gt 10000 ]; then
            local size_kb=$(echo "scale=1; $file_size/1024" | bc)
            echo "   ✓ [$chapter_file] 成功生成 (${size_kb}KB)"
            return 0
        else
            echo "   ✗ [$chapter_file] 文件太小，可能生成失败 (${file_size} bytes)"
            rm -f "$audio_file"
            return 1
        fi
    else
        echo "   ✗ [$chapter_file] 生成失败 (HTTP: $curl_result)"
        rm -f "$audio_file"
        return 1
    fi
}

# 导出函数以便在子进程中使用
export -f process_chapter
export VOLUME_DIR TTS_URL VOICE OUTPUT_DIR

# 获取所有章节文件
cd "$VOLUME_DIR"
chapter_files=($(ls *.txt | sort -V))
total_chapters=${#chapter_files[@]}

echo "📚 发现 $total_chapters 个章节，开始并行处理..."
echo ""

# 使用 xargs 并行处理
printf '%s\n' "${chapter_files[@]}" | xargs -n 1 -P $MAX_JOBS -I {} bash -c 'process_chapter "$@"' _ {}

echo ""
echo "🎉 第一卷有声书生成完成！"
echo "📁 输出目录: $OUTPUT_DIR"

# 统计结果
success_count=$(find "$OUTPUT_DIR" -name "第*.mp3" -type f | wc -l)
echo "📊 成功生成: $success_count/$total_chapters 章节"

echo ""
echo "📋 生成的音频文件："
find "$OUTPUT_DIR" -name "第*.mp3" -type f | sort -V | while read file; do
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
    size_kb=$(echo "scale=1; $size/1024" | bc)
    echo "   $(basename "$file") - ${size_kb}KB"
done

echo ""
echo "🎵 有声书已生成完成，可以开始收听了！"