#!/bin/bash

# 有声书生成脚本
# 使用云希声音生成第一卷有声书

NOVEL_DIR="/Users/xiaoyu/逆天仙途：因果投资万倍返还！"
VOLUME_DIR="$NOVEL_DIR/第一卷 青阳崛起"
OUTPUT_DIR="$NOVEL_DIR/有声书/第一卷_青阳崛起"
TTS_URL="http://192.168.31.252:5000"
VOICE="zh-CN-YunxiNeural"

echo "🎙️  开始生成《逆天仙途：因果投资万倍返还！》有声书"
echo "   使用声音: $VOICE (云希)"
echo "   源目录: $VOLUME_DIR"
echo "   输出目录: $OUTPUT_DIR"
echo "$(printf '%*s' 50 '' | tr ' ' '-')"

# 确保输出目录存在
mkdir -p "$OUTPUT_DIR"

# 计数器
total_files=0
success_files=0

# 获取所有章节文件并按数字顺序排序
cd "$VOLUME_DIR"
for chapter_file in $(ls *.txt | sort -V); do
    echo "🎧 处理章节: $chapter_file"
    
    # 提取章节名称（去掉.txt扩展名）
    chapter_name="${chapter_file%.txt}"
    
    # 读取文件内容，清理格式
    content=$(cat "$chapter_file" | sed 's/^[[:space:]]*[0-9]*→//g' | tr -d '\r' | sed '/^[[:space:]]*$/d' | tr '\n' ' ')
    
    if [ -z "$content" ]; then
        echo "   ✗ 章节内容为空，跳过"
        continue
    fi
    
    # 分割长文本成多个部分（每部分约500字符）
    echo "$content" | fold -w 500 -s | nl -w1 -s'|' | while IFS='|' read -r num text; do
        if [ -n "$text" ] && [ "$(echo "$text" | tr -d ' ')" != "" ]; then
            # 清理文本
            clean_text=$(echo "$text" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed 's/"/\\"/g')
            
            if [ -z "$clean_text" ]; then
                continue
            fi
            
            # 构建输出文件名
            audio_file="$OUTPUT_DIR/${chapter_name}_part$(printf '%02d' $num).mp3"
            
            # 构建JSON请求
            json_data="{\"text\":\"$clean_text\",\"voice\":\"$VOICE\",\"file_name\":\"$(basename "$audio_file")\"}"
            
            # 调用TTS服务
            curl_result=$(curl -s -X POST "$TTS_URL/tts" \
                -H "Content-Type: application/json" \
                -d "$json_data" \
                -o "$audio_file" \
                -w "%{http_code}")
            
            total_files=$((total_files + 1))
            
            if [ "$curl_result" = "200" ] && [ -s "$audio_file" ]; then
                file_size=$(stat -f%z "$audio_file" 2>/dev/null || stat -c%s "$audio_file" 2>/dev/null)
                if [ "$file_size" -gt 1000 ]; then
                    echo "   ✓ 生成音频片段 $num: $(basename "$audio_file") (${file_size} bytes)"
                    success_files=$((success_files + 1))
                else
                    echo "   ✗ 音频片段 $num 文件太小，可能生成失败"
                    rm -f "$audio_file"
                fi
            else
                echo "   ✗ 音频片段 $num 生成失败 (HTTP: $curl_result)"
                rm -f "$audio_file"
            fi
            
            # 短暂延迟避免请求过快
            sleep 1
        fi
    done
    
    echo "   ✓ 章节完成: $chapter_name"
    echo ""
done

echo "🎉 第一卷有声书生成完成！"
echo "📁 输出目录: $OUTPUT_DIR"
echo "📊 共尝试生成 $total_files 个音频文件，成功 $success_files 个"

# 显示生成的文件列表
echo ""
echo "📋 生成的音频文件："
find "$OUTPUT_DIR" -name "*.mp3" -type f | sort | while read file; do
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
    echo "   $(basename "$file") - ${size} bytes"
done