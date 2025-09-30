#!/bin/bash

# 第二卷有声书生成脚本 - 修正版
NOVEL_DIR="/Users/xiaoyu/逆天仙途：因果投资万倍返还！"
VOLUME_DIR="$NOVEL_DIR/第二卷 龙潜于渊"
OUTPUT_DIR="$NOVEL_DIR/有声书/第二卷_龙潜于渊"
TTS_URL="http://192.168.31.252:5000"
VOICE="zh-CN-YunxiNeural"

echo "🎙️  开始生成《第二卷 龙潜于渊》有声书"
echo "   使用云希声音并行处理"
echo "$(printf '%*s' 50 '' | tr ' ' '-')"

mkdir -p "$OUTPUT_DIR"
cd "$VOLUME_DIR"

# 并行处理所有章节
ls *.txt | sort -V | while read -r chapter_file; do
    (
        chapter_name="${chapter_file%.txt}"
        echo "🎵 处理: $chapter_name"
        
        content=$(cat "$chapter_file" | sed 's/^[[:space:]]*[0-9]*→//g' | tr -d '\r' | sed '/^[[:space:]]*$/d' | tr '\n' ' ')
        
        if [ -z "$content" ]; then
            echo "   ✗ 内容为空: $chapter_name"
            exit 1
        fi
        
        clean_text=$(echo "$content" | sed 's/"/\\"/g' | sed 's/\\/\\\\/g')
        audio_file="$OUTPUT_DIR/${chapter_name}.mp3"
        
        curl -s -X POST "$TTS_URL/tts" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"$clean_text\",\"voice\":\"$VOICE\",\"file_name\":\"$(basename "$audio_file")\"}" \
            -o "$audio_file" >/dev/null 2>&1
        
        if [ -s "$audio_file" ]; then
            size=$(stat -f%z "$audio_file" 2>/dev/null || stat -c%s "$audio_file" 2>/dev/null)
            if [ "$size" -gt 10000 ]; then
                size_kb=$(echo "scale=1; $size/1024" | bc)
                echo "   ✓ 完成: $chapter_name (${size_kb}KB)"
            else
                echo "   ✗ 失败: $chapter_name"
                rm -f "$audio_file"
            fi
        else
            echo "   ✗ 生成失败: $chapter_name"
        fi
        
        sleep 0.5
    ) &
    
    # 控制并发
    (($(jobs -r | wc -l) >= 8)) && wait
done

wait
echo "🎉 第二卷生成完成！"
find "$OUTPUT_DIR" -name "*.mp3" | wc -l | xargs echo "📊 成功生成文件数:"