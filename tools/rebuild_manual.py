#!/usr/bin/env python3
"""Rebuild ARKE_Game_Manual.html by replacing sections 03, 07, 08
with the updated pixel-perfect versions from manual_sections/."""

import os

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs')
manual_path = os.path.join(base, 'ARKE_Game_Manual.html')
sections_path = os.path.join(base, 'manual_sections')

# Read the full manual
with open(manual_path, 'r') as f:
    lines = f.readlines()

# Read updated section files
with open(os.path.join(sections_path, '03_characters.html'), 'r') as f:
    new_chars = f.read()
with open(os.path.join(sections_path, '07_worlds.html'), 'r') as f:
    new_worlds = f.read()
with open(os.path.join(sections_path, '08_levels.html'), 'r') as f:
    new_levels = f.read()

# Find section boundaries by searching for marker comments
def find_line(lines, marker, start=0):
    for i in range(start, len(lines)):
        if marker in lines[i]:
            return i
    return -1

# Section 03: Characters
chars_start = find_line(lines, '<!-- Section 03: Characters -->')
chars_end = find_line(lines, '<!-- Section 04: Controls', chars_start + 1)

# Section 07: Worlds
worlds_start = find_line(lines, '<!-- Section 07: Worlds')
worlds_end = find_line(lines, '<!-- Section 08: Level', worlds_start + 1)

# Section 08: Levels
levels_start = find_line(lines, '<!-- Section 08: Level')
levels_end = find_line(lines, '<!-- Section 09: HUD', levels_start + 1)

print(f"Characters: lines {chars_start+1}-{chars_end} (replacing with updated)")
print(f"Worlds: lines {worlds_start+1}-{worlds_end} (replacing with updated)")
print(f"Levels: lines {levels_start+1}-{levels_end} (replacing with updated)")

if any(x < 0 for x in [chars_start, chars_end, worlds_start, worlds_end, levels_start, levels_end]):
    print("ERROR: Could not find all section markers!")
    exit(1)

# Build new file content
# Keep everything before Section 03
new_content = ''.join(lines[:chars_start])
# Add new characters section
new_content += new_chars + '\n'
# Keep everything between Section 04 start and Section 07 start
new_content += ''.join(lines[chars_end:worlds_start])
# Add new worlds section
new_content += new_worlds + '\n'
# Keep everything between Section 08 start and Section 08 start (nothing between 07 end and 08 start)
new_content += ''.join(lines[worlds_end:levels_start])
# Add new levels section
new_content += new_levels + '\n'
# Keep everything from Section 09 onwards
new_content += ''.join(lines[levels_end:])

with open(manual_path, 'w') as f:
    f.write(new_content)

line_count = new_content.count('\n')
size_kb = len(new_content) / 1024
print(f"\nManual rebuilt: {line_count} lines, {size_kb:.0f} KB")
print("Done!")
