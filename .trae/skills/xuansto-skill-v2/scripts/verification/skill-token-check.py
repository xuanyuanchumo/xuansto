import os
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--skill-dir', default=os.getcwd())
args = parser.parse_args()
base = args.skill_dir

with open(os.path.join(base, 'SKILL.md'), 'r', encoding='utf-8') as f:
    content = f.read()

chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
english_words = len(re.findall(r'[a-zA-Z]+', content))
numbers = len(re.findall(r'\d+', content))
punctuation = len(re.findall(r'[^\w\s\u4e00-\u9fff]', content))

chinese_tokens = chinese_chars * 1.5
english_tokens = english_words * 1.3
number_tokens = numbers * 1.0
punct_tokens = punctuation * 0.5

total_tokens = chinese_tokens + english_tokens + number_tokens + punct_tokens

print("=== SKILL.md TOKEN ESTIMATION ===")
print(f"File size: {len(content)} characters")
print(f"Total lines: {len(content.splitlines())}")
print()
print("Content breakdown:")
print(f"  Chinese characters: {chinese_chars} x 1.5 = {chinese_tokens:.0f} tokens")
print(f"  English words: {english_words} x 1.3 = {english_tokens:.0f} tokens")
print(f"  Numbers: {numbers} x 1.0 = {number_tokens:.0f} tokens")
print(f"  Punctuation/symbols: {punctuation} x 0.5 = {punct_tokens:.0f} tokens")
print()
print(f"Estimated total tokens: {total_tokens:.0f}")
print(f"Token limit: 3000")
print()

if total_tokens < 3000:
    print(f"VERDICT: PASS - Token count ({total_tokens:.0f}) is under 3000 limit")
else:
    print(f"VERDICT: FAIL - Token count ({total_tokens:.0f}) EXCEEDS 3000 limit by {total_tokens - 3000:.0f} tokens")

char_estimate = len(content) / 3.5
print()
print(f"Alternative estimate (chars/3.5): {char_estimate:.0f} tokens")
