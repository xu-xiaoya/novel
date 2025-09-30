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

# 获取所有章节文件并按数字顺序排序
cd "$VOLUME_DIR"
for chapter_file in $(ls *.txt | sort -V); do
    echo "🎧 处理章节: $chapter_file"
    
    # 提取章节名称（去掉.txt扩展名）
    chapter_name="${chapter_file%.txt}"
    
    # 读取文件内容，清理格式
    content=$(cat "$chapter_file" | sed 's/^[[:space:]]*[0-9]*→//g' | tr -d '\r' | sed '/^[[:space:]]*$/d')
    
    if [ -z "$content" ]; then
        echo "   ✗ 章节内容为空，跳过"
        continue
    fi
    
    # 将长文本分割成较短的段落（避免TTS请求过长）
    echo "$content" | fold -w 400 -s | nl -w1 -s'|' | while IFS='|' read -r num text; do
        if [ -n "$text" ] && [ "$text" != " " ]; then
            # URL编码文本
            encoded_text=$(echo "$text" | python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.stdin.read().strip()))")
            
            # 构建输出文件名
            audio_file="$OUTPUT_DIR/${chapter_name}_part$(printf '%02d' $num).mp3"
            
            # 调用TTS服务
            curl -s -G "$TTS_URL/tts" \
                --data-urlencode "text=$text" \
                --data-urlencode "voice=$VOICE" \
                --data-urlencode "rate=+0%" \
                --data-urlencode "pitch=+0Hz" \
                -o "$audio_file"
            
            if [ $? -eq 0 ] && [ -s "$audio_file" ]; then
                echo "   ✓ 生成音频片段 $num: $(basename "$audio_file")"
            else
                echo "   ✗ 音频片段 $num 生成失败"
                rm -f "$audio_file"
            fi
            
            # 短暂延迟避免请求过快
            sleep 0.5
        fi
    done
    
    echo "   ✓ 章节完成: $chapter_name"
    echo ""
done

echo "🎉 第一卷有声书生成完成！"
echo "📁 输出目录: $OUTPUT_DIR"

# 显示生成的文件数量
file_count=$(find "$OUTPUT_DIR" -name "*.mp3" | wc -l)
echo "📊 共生成 $file_count 个音频文件"