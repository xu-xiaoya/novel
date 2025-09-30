#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import re
from pathlib import Path
import time
import urllib.parse

class AudiobookGenerator:
    def __init__(self, tts_url="http://192.168.31.252:5000"):
        self.tts_url = tts_url
        self.voice = "zh-CN-YunxiNeural"  # 云希声音
        self.rate = "+0%"  # 正常语速
        self.pitch = "+0Hz"  # 正常音调
        
    def clean_text(self, text):
        """清理文本，移除序号等格式符号"""
        # 移除行首的序号 (如: "1→", "123→")
        text = re.sub(r'^\s*\d+→', '', text)
        # 移除多余的空白行
        text = re.sub(r'\n\s*\n', '\n', text)
        # 移除首尾空白
        text = text.strip()
        return text
    
    def split_long_text(self, text, max_length=500):
        """将长文本按句子分割成较短的段落"""
        sentences = re.split(r'[。！？…]', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果当前句子本身就很长，强制分割
            if len(sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                chunks.append(sentence[:max_length])
                if len(sentence) > max_length:
                    chunks.append(sentence[max_length:])
            # 如果加上当前句子会超过限制，先保存当前块
            elif len(current_chunk) + len(sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += "。" + sentence
                else:
                    current_chunk = sentence
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def text_to_speech(self, text, output_file):
        """将文本转换为语音"""
        try:
            # 构建请求URL
            params = {
                'text': text,
                'voice': self.voice,
                'rate': self.rate,
                'pitch': self.pitch
            }
            
            response = requests.get(f"{self.tts_url}/tts", params=params, timeout=30)
            
            if response.status_code == 200:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"✓ 生成音频: {output_file}")
                return True
            else:
                print(f"✗ TTS请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 生成音频时出错: {e}")
            return False
    
    def generate_chapter_audio(self, chapter_file, output_dir):
        """为单个章节生成音频"""
        try:
            # 读取章节内容
            with open(chapter_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 清理文本
            content = self.clean_text(content)
            if not content:
                print(f"✗ 章节内容为空: {chapter_file}")
                return False
            
            # 获取章节名称
            chapter_name = Path(chapter_file).stem
            print(f"🎧 开始生成章节: {chapter_name}")
            
            # 分割长文本
            text_chunks = self.split_long_text(content)
            print(f"   分割为 {len(text_chunks)} 个音频片段")
            
            # 为每个文本块生成音频
            audio_files = []
            for i, chunk in enumerate(text_chunks):
                if not chunk.strip():
                    continue
                    
                audio_file = os.path.join(output_dir, f"{chapter_name}_part{i+1:02d}.mp3")
                if self.text_to_speech(chunk, audio_file):
                    audio_files.append(audio_file)
                    time.sleep(0.5)  # 避免请求过快
                else:
                    print(f"✗ 片段 {i+1} 生成失败")
            
            print(f"✓ 章节完成: {chapter_name} ({len(audio_files)} 个音频文件)")
            return True
            
        except Exception as e:
            print(f"✗ 处理章节时出错 {chapter_file}: {e}")
            return False
    
    def generate_volume_audio(self, volume_dir, output_dir):
        """为整个卷生成音频"""
        volume_path = Path(volume_dir)
        if not volume_path.exists():
            print(f"✗ 卷目录不存在: {volume_dir}")
            return False
        
        # 获取所有章节文件
        chapter_files = sorted([f for f in volume_path.glob("*.txt")])
        if not chapter_files:
            print(f"✗ 在目录中未找到章节文件: {volume_dir}")
            return False
        
        print(f"📚 开始生成卷: {volume_path.name}")
        print(f"   共 {len(chapter_files)} 章")
        
        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 为每个章节生成音频
        success_count = 0
        for chapter_file in chapter_files:
            if self.generate_chapter_audio(chapter_file, output_dir):
                success_count += 1
        
        print(f"🎉 卷完成: {success_count}/{len(chapter_files)} 章节成功生成")
        return success_count > 0

def main():
    generator = AudiobookGenerator()
    
    # 设置路径
    novel_dir = "/Users/xiaoyu/逆天仙途：因果投资万倍返还！"
    volume1_dir = os.path.join(novel_dir, "第一卷 青阳崛起")
    output_dir = os.path.join(novel_dir, "有声书", "第一卷_青阳崛起")
    
    print("🎙️  开始生成《逆天仙途：因果投资万倍返还！》有声书")
    print(f"   使用声音: {generator.voice} (云希)")
    print(f"   源目录: {volume1_dir}")
    print(f"   输出目录: {output_dir}")
    print("-" * 50)
    
    # 生成第一卷音频
    if generator.generate_volume_audio(volume1_dir, output_dir):
        print("\n🎉 第一卷有声书生成完成！")
    else:
        print("\n❌ 生成过程中出现错误")

if __name__ == "__main__":
    main()