# -*- coding: utf-8 -*-
"""
批量移除tests目录中的emoji
"""

import os

def remove_emoji_from_tests():
    """移除tests目录中的emoji"""
    tests_dir = os.path.join(os.path.dirname(__file__), '..', 'tests')
    tests_dir = os.path.abspath(tests_dir)

    emoji_replacements = [
        ('✓', '[OK]'),
        ('✗', '[FAIL]'),
        ('⚠', '[WARN]'),
        ('✨', '[INFO]'),
        ('❌', '[ERROR]'),
    ]

    processed = 0
    for root, dirs, files in os.walk(tests_dir):
        dirs[:] = [d for d in dirs if d != '__pycache__']

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                original = content
                for emoji, replacement in emoji_replacements:
                    content = content.replace(emoji, replacement)

                if content != original:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Processed: {file_path}")
                    processed += 1

    return processed

if __name__ == '__main__':
    count = remove_emoji_from_tests()
    print(f"\nTotal test files processed: {count}")

