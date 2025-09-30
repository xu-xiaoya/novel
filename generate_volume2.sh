#!/bin/bash

# 有声书生成脚本 - 第二卷专用并行版本
# 使用云希声音生成第二卷有声书

NOVEL_DIR="/Users/xiaoyu/逆天仙途：因果投资万倍返还！"
VOLUME_DIR="$NOVEL_DIR/第二卷 龙潜于渊"
OUTPUT_DIR="$NOVEL_DIR/有声书/第二卷_龙潜于渊"
TTS_URL="http://192.168.31.252:5000"
VOICE="zh-CN-YunxiNeural"
MAX_JOBS=6  # 增加并行任务数

echo "🎙️  开始生成《第二卷 龙潜于渊》有声书"
echo "   使用声音: $VOICE (云希)"
echo "   并行任务数: $MAX_JOBS"
echo "   源目录: $VOLUME_DIR"
echo "   输出目录: $OUTPUT_DIR"
echo "$(printf '%*s' 50 '' | tr ' ' '-')"

# 确保输出目录存在
mkdir -p "$OUTPUT_DIR"

cd "$VOLUME_DIR"
chapter_files=($(ls *.txt | sort -V))
total_chapters=${#chapter_files[@]}

echo "📚 发现 $total_chapters 个章节，开始并行处理..."

# 使用后台任务并行处理
for chapter_file in "${chapter_files[@]}"; do
    (
        chapter_name="${chapter_file%.txt}"
        echo "🎧 处理章节: $chapter_file"
        
        content=$(cat "$chapter_file" | sed 's/^[[:space:]]*[0-9]*→//g' | tr -d '\r' | sed '/^[[:space:]]*$/d' | tr '\n' ' ')
        
        if [ -z "$content" ]; then
            echo "   ✗ [$chapter_file] 内容为空，跳过"
            exit 1
        fi
        
        clean_text=$(echo "$content" | sed 's/"/\\"/g' | sed 's/\\/\\\\/g')
        audio_file="$OUTPUT_DIR/${chapter_name}.mp3"
        json_data="{\"text\":\"$clean_text\",\"voice\":\"$VOICE\",\"file_name\":\"$(basename "$audio_file")\"}"
        
        curl_result=$(curl -s -X POST "$TTS_URL/tts" \
            -H "Content-Type: application/json" \
            -d "$json_data" \
            -o "$audio_file" \
            -w "%{http_code}")
        
        if [ "$curl_result" = "200" ] && [ -s "$audio_file" ]; then
            file_size=$(stat -f%z "$audio_file" 2>/dev/null || stat -c%s "$audio_file" 2>/dev/null)
            if [ "$file_size" -gt 10000 ]; then
                size_kb=$(echo "scale=1; $file_size/1024" | bc)
                echo "   ✓ [$chapter_file] 成功 (${size_kb}KB)"
            else
                echo "   ✗ [$chapter_file] 文件太小"
                rm -f "$audio_file"
            fi
        else
            echo "   ✗ [$chapter_file] 失败 (HTTP: $curl_result)"
            rm -f "$audio_file"
        fi
    ) &
    
    # 控制并发数量
    (($(jobs -r | wc -l) >= MAX_JOBS)) && wait
done

# 等待所有任务完成
wait

echo ""
echo "🎉 第二卷有声书生成完成！"

success_count=$(find "$OUTPUT_DIR" -name "第*.mp3" -type f | wc -l)
echo "📊 成功生成: $success_count/$total_chapters 章节"

echo ""
echo "📋 生成的音频文件："
find "$OUTPUT_DIR" -name "第*.mp3" -type f | sort -V | while read file; do
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
    size_kb=$(echo "scale=1; $size/1024" | bc)
    echo "   $(basename "$file") - ${size_kb}KB"
done