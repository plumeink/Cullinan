# -*- coding: utf-8 -*-
"""
批量移除日志中的emoji和制表符装饰
保留启动banner
"""

import os
import re

def remove_decorations(file_path):
    """移除文件中的emoji和制表符装饰"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 定义需要替换的emoji及其文本替换
    emoji_replacements = [
        ('✓', '[OK]'),
        ('✗', '[FAIL]'),
        ('⚠', '[WARN]'),
        ('✨', '[INFO]'),
        ('❌', '[ERROR]'),
        ('🔧', '[CONFIG]'),
        ('🚀', '[START]'),
        ('📦', '[PACKAGE]'),
        ('🔍', '[SEARCH]'),
        ('⏱', '[TIMER]'),
        ('💡', '[TIP]'),
        ('🎯', '[TARGET]'),
        ('🔄', '[RELOAD]'),
        ('📝', '[NOTE]'),
        ('🌐', '[NETWORK]'),
        ('🔌', '[PLUGIN]'),
        ('🎉', '[SUCCESS]'),
        ('⚡', '[FAST]'),
        ('🛠', '[TOOL]'),
        ('📊', '[STATS]'),
        ('🔥', '[HOT]'),
        ('💉', '[INJECT]'),
        ('🏗', '[BUILD]'),
        ('🎨', '[STYLE]'),
        ('🧪', '[TEST]'),
        ('🔐', '[SECURE]'),
        ('📡', '[SIGNAL]'),
        ('🎭', '[MOCK]'),
        ('🔗', '[LINK]'),
        ('📋', '[LIST]'),
        ('⚙', '[SETTING]'),
        ('🌟', '[NEW]'),
        ('💫', '[MAGIC]'),
        ('🚨', '[ALERT]'),
        ('🔔', '[NOTIFY]'),
        ('📢', '[ANNOUNCE]'),
        ('🎪', '[EVENT]'),
        ('🏁', '[FINISH]'),
        ('🎬', '[ACTION]'),
        ('•', '[INFO]'),
    ]
    
    # 替换emoji
    for emoji, replacement in emoji_replacements:
        content = content.replace(emoji, replacement)
    
    # 移除制表符装饰 \t|||\t (但保留BANNER定义)
    # 处理logger调用中的制表符装饰
    lines = content.split('\n')
    new_lines = []
    in_banner = False
    
    for line in lines:
        # 检测BANNER定义的开始和结束
        if 'BANNER = (' in line:
            in_banner = True
        
        # 如果在BANNER定义中，保持原样
        if in_banner:
            new_lines.append(line)
            if line.strip() == ')':
                in_banner = False
            continue
        
        # 如果是logger调用，移除制表符装饰
        if 'logger.' in line and '\t|||\t' in line:
            # 替换 \t|||\t\t\t 为空
            line = line.replace('\t|||\t\t\t', '')
            # 替换 \t|||\t\t 为空
            line = line.replace('\t|||\t\t', '')
            # 替换 \t|||\t 为空
            line = line.replace('\t|||\t', '')
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # 只有内容改变时才写入
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def process_directory(directory):
    """处理目录中的所有Python文件"""
    processed = 0
    for root, dirs, files in os.walk(directory):
        # 跳过__pycache__等目录
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if remove_decorations(file_path):
                    print(f"Processed: {file_path}")
                    processed += 1
    
    return processed

if __name__ == '__main__':
    # 处理cullinan包
    cullinan_dir = os.path.join(os.path.dirname(__file__), '..', 'cullinan')
    cullinan_dir = os.path.abspath(cullinan_dir)
    
    print(f"Processing directory: {cullinan_dir}")
    count = process_directory(cullinan_dir)
    print(f"\nTotal files processed: {count}")

