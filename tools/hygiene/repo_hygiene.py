#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Repository hygiene checks shared by the rivendale open-source repos.

    python3 tools/hygiene/repo_hygiene.py [--root DIR] [--config .hygiene.json] [--base REF]
    python3 tools/hygiene/repo_hygiene.py --print-root-safety    the config's root_safety commands, one per line
    python3 tools/hygiene/repo_hygiene.py --selftest             check the checker in a temp git repo, no network

Checks, each configured in the repo's .hygiene.json (schema: tools/hygiene/README.md):
  modes         a tracked file with a shebang went from 100755 to 100644 between the merge base of --base and HEAD
                (pushing through the GitHub API resets modes)
  invisible     a raw character a reader cannot see in a tracked text file or path: every format (Cf) and control (Cc)
                character except tab, LF, CR, FF and VT, every Default_Ignorable_Code_Point, U+2800, the noncharacters,
                U+2028 and U+2029, and a variation selector outside a sequence Unicode defines (every ideographic
                one); also a text file that is not valid UTF-8.
                Bidi controls are Trojan Source (CVE-2021-42574). A BOM at file start is allowed. Binary files
                (git's rule: a NUL in the first 8000 bytes, or -text / binary in .gitattributes) are skipped.
  claims        a number written in a file disagrees with a count taken from the repo ("12 skills" vs skills/*/SKILL.md)
  stale         a dated marker ("checked YYYY-MM-DD") older than max_age_days; fenced code blocks are skipped;
                a warning unless stale_fails is true
  instructions  an agent instruction file is over its byte limit, or its sentinel line is missing or not the last line
With --base, a change that loosens .hygiene.json against the base prints a notice.
Root safety (running commands as root in a throwaway container) is tools/hygiene/root_safety.sh, run by
.github/workflows/hygiene.yml.

Exit 0 when clean, 1 on any failure (warnings print but do not fail), 2 when the config is unreadable or invalid.
Standard library only; needs git on PATH.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

DEFAULTS = {
    "modes": True,
    "invisible": True,
    "invisible_allow": [],
    "claims": [],
    "stale": True,
    "stale_pattern": r"\b(?:checked|verified|as of)[:\s]+(\d{4}-\d{2}-\d{2})\b",
    "stale_globs": ["**/*.md"],
    "stale_exclude": [],
    "max_age_days": 45,
    "stale_fails": False,
    "instructions": [],
    "root_safety": [],
}
CLAIM_KEYS = {"file", "pattern", "count_glob", "count_json", "count_lines"}
INSTRUCTION_KEYS = {"file", "max_bytes", "sentinel"}
BIDI = set("\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")
BOM = "\ufeff"


class ConfigError(Exception):
    pass


# ---------------------------------------------------------------- helpers

def git(root, *args, text=True):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=text, check=True).stdout


def tracked(root):
    return [p for p in git(root, "ls-files", "-z").split("\0") if p]


# Default_Ignorable_Code_Point: characters a renderer shows as nothing. From the Unicode Character Database,
# DerivedCoreProperties.txt (https://www.unicode.org/Public/UCD/latest/ucd/DerivedCoreProperties.txt); this list was
# checked against the 18.0.0 draft of 2026-08-07 in github.com/unicode-org/unicodetools. It covers the bidi controls,
# zero-width characters, the Hangul fillers, the variation selectors and the whole U+E0000 to U+E0FFF block (tags and
# the reserved code points after them, which also smuggle text).
DEFAULT_IGNORABLE = ((0x00AD, 0x00AD), (0x034F, 0x034F), (0x061C, 0x061C), (0x115F, 0x1160), (0x17B4, 0x17B5),
                     (0x180B, 0x180F), (0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x206F), (0x3164, 0x3164),
                     (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF), (0xFFA0, 0xFFA0), (0xFFF0, 0xFFF8), (0x1BCA0, 0x1BCA3),
                     (0x1D173, 0x1D17A), (0xE0000, 0xE0FFF))
# Blank-looking but not default-ignorable: the braille blank.
EXTRA_HIDDEN = {0x2800}
# The only control characters allowed raw. str.isspace() would also let 0x1C-0x1F and U+0085 through.
WHITESPACE = set("\t\n\r\f\v")
VS_RX = re.compile("[\U0000FE00-\U0000FE0F\U000E0100-\U000E01EF]")
# The characters that take U+FE0E or U+FE0F, from emoji-variation-sequences.txt (Unicode emoji data,
# https://www.unicode.org/Public/UCD/latest/ucd/emoji/emoji-variation-sequences.txt; this list is the 19.0.0 draft of
# 2026-09-21 in github.com/unicode-org/unicodetools). Hex code points and ranges.
EMOJI_VS_BASES = (
    "23 2A 30-39 A9 AE 203C 2049 2122 2139 2194-2199 21A9-21AA 231A-231B 2328 23CF 23E9-23F3 23F8-23FA 24C2 "
    "25AA-25AB 25B6 25C0 25FB-25FE 2600-2604 260E 2611 2614-2615 2618 261D 2620 2622-2623 2626 262A 262E-262F "
    "2638-263A 2640 2642 2648-2653 265F-2660 2663 2665-2666 2668 267B 267E-267F 2692-2697 2699 269B-269C "
    "26A0-26A1 26A7 26AA-26AB 26B0-26B1 26BD-26BE 26C4-26C5 26C8 26CE-26CF 26D1 26D3-26D4 26E9-26EA 26F0-26F5 "
    "26F7-26FA 26FD 2702 2705 2708-270D 270F 2712 2714 2716 271D 2721 2728 2733-2734 2744 2747 274C 274E "
    "2753-2755 2757 2763-2764 2795-2797 27A1 27B0 27BF 2934-2935 2B05-2B07 2B1B-2B1C 2B50 2B55 3030 303D 3297 "
    "3299 1F004 1F170-1F171 1F17E-1F17F 1F202 1F21A 1F22F 1F237 1F30D-1F30F 1F315 1F31C 1F321 1F324-1F32C "
    "1F336 1F378 1F37D 1F393 1F396-1F397 1F399-1F39B 1F39E-1F39F 1F3A7 1F3AC-1F3AE 1F3C2 1F3C4 1F3C6 "
    "1F3CA-1F3CE 1F3D4-1F3E0 1F3ED 1F3F3 1F3F5 1F3F7 1F408 1F415 1F41F 1F426 1F43F 1F441-1F442 1F446-1F449 "
    "1F44D-1F44E 1F453 1F46A 1F47D 1F4A3 1F4B0 1F4B3 1F4BB 1F4BF 1F4CB 1F4DA 1F4DF 1F4E4-1F4E6 1F4EA-1F4ED "
    "1F4F7 1F4F9-1F4FB 1F4FD 1F508 1F50D 1F512-1F513 1F549-1F54A 1F550-1F567 1F56F-1F570 1F573-1F579 1F587 "
    "1F58A-1F58D 1F590 1F5A5 1F5A8 1F5B1-1F5B2 1F5BC 1F5C2-1F5C4 1F5D1-1F5D3 1F5DC-1F5DE 1F5E1 1F5E3 1F5E8 "
    "1F5EF 1F5F3 1F5FA 1F610 1F687 1F68D 1F691 1F694 1F698 1F6AD 1F6B2 1F6B9-1F6BA 1F6BC 1F6CB 1F6CD-1F6CF "
    "1F6E0-1F6E5 1F6E9 1F6F0 1F6F3 "
)
# The base and selector pairs for U+FE00 to U+FE0D, from StandardizedVariants.txt (Unicode Character Database,
# https://www.unicode.org/Public/UCD/latest/ucd/StandardizedVariants.txt; this list is the 18.0.0 draft of 2026-07-29
# in github.com/unicode-org/unicodetools). Selector: hex code points and ranges of the bases it is defined for.
STANDARDIZED_VARIANTS = {
    0xFE00: (
        "30 1000 1002 1004 1010-1011 1015 1019-101A 101C-101D 1022 1031 1075 1078 107A 1080 2018-2019 "
        "201C-201D 210B 2110 2112 211B 212C 2130-2131 2133 2205 2229-222A 223D 2242-2243 2248 2268-2269 "
        "2272-2273 228A-228B 2293-2295 2297 229C 22CD 22DA-22DD 29B7 2A3C-2A3D 2A6C 2A9D-2A9E 2AAC-2AAD "
        "2ACB-2ACC 3001-3002 31C0 31C6 31C9 31CF-31D2 31D4-31D5 31D7 31DB-31DD 31E5 349E 34B9 34BB 34DF 3515 "
        "36EE 36FC 3781 382F 3862 387C 38C7 38E3 391C 393A 3A2E 3A6C 3AE4 3B08 3B19 3B49 3B9D 3C18 3C4E 3D33 "
        "3D96 3EAC 3EB8 3F1B 3FFC 4008 4018 4039 4046 4096 40E3 412F 4202 4227 42A0 4301 4334 4359 43D5 43D9 "
        "440B 446B 452B 455D 4561 456B 45D7 45F9 4635 46BE 46C7 4995 49E6 4A6E 4A76 4AB2 4B33 4BCE 4CCE 4CED "
        "4CF8 4D56 4E0D 4E26 4E32 4E38-4E39 4E3D 4E41 4E82 4E86 4EAE 4EC0 4ECC 4EE4 4F60 4F80 4F86 4F8B 4FAE "
        "4FBB 4FBF 5002 502B 507A 5099 50CF 50DA 50E7 5140 5145 514D 5154 5164 5167-5169 516D 5177 5180 518D "
        "5192 5195 5197 51A4 51AC 51B5 51B7 51C9 51CC 51DC 51DE 51F5 5203 5207 5217 5229 523A-523B 5246 5272 "
        "5277 5289 529B 52A3 52B3 52C7 52C9 52D2 52DE 52E4 52F5 52FA 5305-5306 5317 533F 5349 5351 535A 5373 "
        "5375 537D 537F 53C3 53CA 53DF 53E5 53EB 53F1 5406 540F 541D 5438 5442 5448 5468 549E 54A2 54BD 54F6 "
        "5510 5553 5555 5563 5584 5587 5599 559D 55AB 55B3 55C0 55C2 55E2 5606 5651 5668 5674 56F9 5716-5717 "
        "578B 57CE 57F4 580D 5831-5832 5840 585A 585E 58A8 58AC 58B3 58D8 58DF 58EE 58F2 58F7 5906 591A 5922 "
        "5944 5948 5951 5954 5962 5973 59D8 59EC 5A1B 5A27 5A62 5A66 5AB5 5B08 5B28 5B3E 5B85 5BC3 5BD8 5BE7 "
        "5BEE 5BF3 5BFF 5C06 5C22 5C3F 5C60 5C62 5C64-5C65 5C6E 5C8D 5CC0 5D19 5D43 5D50 5D6B 5D6E 5D7C 5DB2 "
        "5DBA 5DE1-5DE2 5DFD 5E28 5E3D 5E69 5E74 5EA6 5EB0 5EB3 5EB6 5EC9-5ECA 5ED2-5ED3 5ED9 5EEC 5EFE 5F04 "
        "5F22 5F53 5F62 5F69 5F6B 5F8B 5F9A 5FA9 5FAD 5FCD 5FD7 5FF5 5FF9 6012 601C 6075 6081 6094 60C7 60D8 "
        "60E1 6108 6144 6148 614C 614E 6160 6168 617A 618E 6190 61A4 61AF 61B2 61DE 61F2 61F6 6200 6210 621B "
        "622E 6234 625D 62B1 62C9 62CF 62D3-62D4 62FC 62FE 633D 6350 6368 637B 6383 63A0 63A9 63C4-63C5 63E4 "
        "641C 6422 6452 6469 6477 647E 649A 649D 64C4 654F 6556 656C 6578 6599 65C5 65E2-65E3 6613 6649 6674 "
        "6688 6691 669C 66B4 66C6 66F4 66F8 6700 6717 671B 6721 674E 6753 6756 675E 677B 6785 6797 67F3 67FA "
        "6817 681F 6852 6881 6885 688E 68A8 6914 6942 69A3 69EA 6A02 6A13 6AA8 6AD3 6ADB 6B04 6B21 6B54 6B72 "
        "6B77 6B79 6B9F 6BAE 6BBA-6BBB 6C4E 6C67 6C88 6CBF 6CCC-6CCD 6CE5 6D16 6D1B 6D1E 6D34 6D3E 6D41 "
        "6D69-6D6A 6D77-6D78 6D85 6DCB 6DDA 6DEA 6DF9 6E1A 6E2F 6E6E 6E9C 6EBA 6EC7 6ECB 6ED1 6EDB 6F0F "
        "6F22-6F23 6F6E 6FC6 6FEB 6FFE 701B 701E 7039 704A 7070 7077 707D 7099 70AD 70C8 70D9 7145 7149 716E "
        "719C 71CE 71D0 7210 721B 7228 722B 7235 7250 7262 7280 7295 72AF 72C0 72FC 732A 7375 737A 7387 738B "
        "73A5 73B2 73DE 7406 7409 7422 7447 745C 7469 7471 7485 7489 7498 74CA 7506 7524 753B 753E 7559 7565 "
        "7570 75E2 7610 761D 761F 7642 7669 76CA 76DB 76E7 76F4 7701 771E-771F 7740 774A 778B 77A7 784E 786B "
        "788C 7891 78CA 78CC 78FB 792A 793C 793E 7948-7949 7950 7956 795D-795E 7965 797F 798D-798F 79AE 79CA "
        "79EB 7A1C 7A40 7A4A 7A4F 7A81 7AB1 7ACB 7AEE 7B20 7BC0 7BC6 7BC9 7C3E 7C60 7C7B 7C92 7CBE 7CD2 7CD6 "
        "7CE3 7CE7-7CE8 7D00 7D10 7D22 7D2F 7D5B 7D63 7DA0 7DBE 7DC7 7DF4 7E02 7E09 7E37 7E41 7E45 7F3E 7F72 "
        "7F79-7F7A 7F85 7F95 7F9A 7FBD 7FFA 8001 8005 8046 8060 806F-8070 807E 808B 80AD 80B2 8103 813E 81D8 "
        "81E8 81ED 8201 8204 8218 826F 8279 828B 8291 829D 82B1 82B3 82BD 82E5-82E6 831D 8323 8336 8352-8353 "
        "8363 83AD 83BD 83C9-83CA 83CC 83DC 83E7 83EF 83F1 843D 8449 8457 84EE 84F1 84F3 84FC 8516 8564 85CD "
        "85FA 8606 8612 862D 863F 8650 865C 8667 8669 8688 86A9 86E2 870E 8728 876B 8779 8786 87BA 87E1 8801 "
        "881F 884C 8860 8863 88C2 88CF 88D7 88DE 88E1 88F8 88FA 8910 8941 8964 8986 898B 8996 8AA0 8AAA 8ABF "
        "8ACB 8AD2 8AD6 8AED 8AF8 8AFE 8B01 8B39 8B58 8B80 8B8A 8C48 8C55 8CAB 8CC1-8CC2 8CC8 8CD3 8D08 8D1B "
        "8D77 8DBC 8DCB 8DEF-8DF0 8ECA 8ED4 8F26 8F2A 8F38 8F3B 8F62 8F9E 8FB0 8FB6 9023 9038 9072 907C 908F "
        "9094 90CE 90DE 90F1 90FD 9111 911B 916A 9199 91B4 91CC 91CF 91D1 9234 9238 9276 927C 92D7-92D8 9304 "
        "934A 93F9 9415 958B 95AD 95B7 962E 964B 964D 9675 9678 967C 9686 96A3 96B7-96B8 96C3 96E2-96E3 "
        "96F6-96F7 9723 9732 9748 9756 97DB 97E0 97FF 980B 9818 9829 983B 985E 98E2 98EF 98FC 9928-9929 99A7 "
        "99C2 99F1 99FE 9A6A 9B12 9B6F 9C40 9C57 9CFD 9D67 9DB4 9DFA 9E1E 9E7F 9E97 9E9F 9EBB 9ECE 9EF9 9EFE "
        "9F05 9F0F 9F16 9F3B 9F43 9F8D-9F8E 9F9C A856 A85C A85E-A860 A868 AA60-AA66 AA6B-AA6C AA6F AA7A FF01 "
        "FF0C FF0E FF10 FF1A-FF1B FF1F 10AC5-10AC6 10AD6-10AD7 10AE1 13091 1310F 1311C 13121 13127 13139 "
        "131A0 131B1 131B8-131B9 131CB 131E0 131F9-131FA 1327B 1327F 13285 1328C 132AA 132CB 132DC 132E7 "
        "13307 1331B 13322 1333C 13377-13378 13399-1339A 133D3 133E4-133E5 133E7 133EE 133F2 133F5-133F6 "
        "13416 13419-1341A 13423 13443-13446 13BE8-13BEA 13F72 1D49C 1D49E-1D49F 1D4A2 1D4A5-1D4A6 "
        "1D4A9-1D4AC 1D4AE-1D4B5 1DB10 20122 2051C 20525 2054B 2063A 20804 208DE 20A2C 20B63 214E4 216A8 "
        "216EA 219C8 21B18 21D0B 21DE4 21DE6 22183 2219F 22331 226D4 22844 2284A 22B0C 22BF1 2300A 232B8 "
        "2335F 23393 2339C 233C3 233D5 2346D 236A3 238A7 23A8D 23AFA 23CBC 23D1E 23ED1 23F5E 23F8E 24263 "
        "242EE 243AB 24608 24735 24814 24C36 24C92 24FA1 24FB8 25044 250F2-250F3 25119 25133 25249 2541D "
        "25626 2569A 256C5 2597C 25AA7 25BAB 25C80 25CD0 25F86 261DA 26228 26247 262D9 2633E 264DA 26523 "
        "265A8 267A7 267B5 26B3C 26C36 26CD5 26D6B 26F2C 26FB1 270D2 273CA 27667 278AE 27966 27CA8 27ED3 "
        "27F2F 285D2 285ED 2872E 28BFA 28D77 29145 291DF 2921A 2940A 29496 295B6 29B30 2A0CE 2A105 2A20E "
        "2A291 2A392 2A600 "
    ),
    0xFE01: (
        "2018-2019 201C-201D 210B 2110 2112 211B 212C 2130-2131 2133 3001-3002 31C6 31CF 31DD 3B9D 3EB8 4039 "
        "4FAE 50E7 514D 51B5 5207 52C7 52C9 52E4 52FA 5317 5351 537F 5584 5599 559D 5606 585A 5B3E 5BE7 5C6E "
        "5ECA 5F22 6094 614C 614E 618E 61F2 61F6 654F 6674 6691 6717 671B 6885 6A02 6BBA 6D41 6D77 6ECB 6F22 "
        "701E 716E 7235 732A 7387 7471 7570 76CA 76F4 771F 774A 788C 78CC 7956 798F 7A40 7BC0 7DF4 8005 8201 "
        "8279 82E5 8457 865C 8779 8996 8AAA 8AED 8AF8 8AFE 8B01 8B39 8B8A 8D08 8F38 9038 96E3 9756 97FF 980B "
        "983B 9B12 9F9C FF01 FF0C FF0E FF1A-FF1B FF1F 13093 13132 13139 13187 131B1 131EE 131F8-131FA 13257 "
        "1327F 1328B 132A4 13308 13312-13314 1331B 13321-13322 13331 133E8 13419 13F1F 14274 1D49C "
        "1D49E-1D49F 1D4A2 1D4A5-1D4A6 1D4A9-1D4AC 1D4AE-1D4B5 22331 25AA7 "
    ),
    0xFE02: (
        "2018-2019 201C-201D 537F 5BE7 618E 61F2 6717 6A02 6BBA 6D41 7DF4 8005 980B 9F9C 13117 13139 13183 "
        "131A0 131BA 131EE 13216 1327B 132A4 132E7 132E9 132F8 132FD 13302-13303 13310-13314 1331C 13321 "
        "13331 1334A 13361 13373 1337D 13385 133AF-133B0 133BF 133DB 133DD 13419 1342C 1342E 14274 1D4CF "
    ),
    0xFE03: (
        "13012 130B8 130BA 1310F 1312F 13139 13184 1319C-1319D 1319F 131B1 131DB 13205 13296 13338 13419 "
    ),
    0xFE04: (
        "13139 1340D "
    ),
    0xFE05: (
        "13139 14274 "
    ),
    0xFE06: (
        "1312F 13139 13184 131DB 131EE 13205 132A4 132E9 1332B 13338 13370-13371 13419 14274 "
    ),
}
# Noncharacters: U+FDD0 to U+FDEF and the last two code points of every plane.
NONCHARACTERS = {*range(0xFDD0, 0xFDF0), *(plane << 16 | low for plane in range(17) for low in (0xFFFE, 0xFFFF))}
KEYCAP_BASES = set("#*0123456789")


def _ranges(text):
    out = []
    for tok in text.split():
        a, _, b = tok.partition("-")
        out.append((int(a, 16), int(b or a, 16)))
    return tuple(out)


EMOJI_VS = _ranges(EMOJI_VS_BASES)
SV_BASES = {vs: _ranges(text) for vs, text in STANDARDIZED_VARIANTS.items()}


def is_variation_selector(cp):
    return 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF


def is_hidden(ch):
    """A character a reader cannot see: every Default_Ignorable_Code_Point (which covers the reserved invisible code
    points), EXTRA_HIDDEN, the noncharacters, every Cf and Cc character except the five whitespace controls (the
    strip_hidden() set in tools/build_catalog.py, without the extra controls isspace() exempts), and the line and
    paragraph separators (Zl, Zp: U+2028 and U+2029 end a line in JavaScript, so code after them runs unseen).
    Other unassigned code points are not flagged: they may be characters newer than this Python's Unicode tables.
    Variation selectors are left to vs_ok(), which judges them by the character before them."""
    cp = ord(ch)
    if is_variation_selector(cp):
        return False
    if cp in EXTRA_HIDDEN or cp in NONCHARACTERS or any(a <= cp <= b for a, b in DEFAULT_IGNORABLE):
        return True
    return ch not in WHITESPACE and unicodedata.category(ch) in ("Cf", "Cc", "Zl", "Zp")


def vs_ok(prev, vs):
    """True when the variation selector vs directly follows a character it is defined for. U+FE0E and U+FE0F: a
    base listed in emoji-variation-sequences.txt; of ASCII only the keycap bases, and only with U+FE0F. U+FE00 to
    U+FE0D: the pairs in StandardizedVariants.txt. U+E0100 and up (ideographic variation selectors): never, since
    any ideograph can carry one; a repo that uses ideographic variation sequences allow-lists those files."""
    if not prev:
        return False
    cp, v = ord(prev), ord(vs)
    within = lambda ranges: any(a <= cp <= b for a, b in ranges)
    if v >= 0xE0100:
        return False
    if cp < 0x80 and v in (0xFE0E, 0xFE0F):
        return prev in KEYCAP_BASES and v == 0xFE0F
    if v in (0xFE0E, 0xFE0F):
        return within(EMOJI_VS)
    return within(SV_BASES.get(v, ()))


def _hidden_rx():
    ranges, start, prev = [], None, None
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF or not is_hidden(chr(cp)):
            continue
        if start is not None and cp == prev + 1:
            prev = cp
            continue
        if start is not None:
            ranges.append((start, prev))
        start = prev = cp
    ranges.append((start, prev))
    return re.compile("[" + "".join(re.escape(chr(a)) if a == b else f"{re.escape(chr(a))}-{re.escape(chr(b))}"
                                    for a, b in ranges) + "]")


HIDDEN = _hidden_rx()
HIDDEN_RUN = re.compile(HIDDEN.pattern + "+")


def describe(ch):
    cp = ord(ch)
    cat = unicodedata.category(ch)
    kind = "bidi control" if ch in BIDI else "tag character" if 0xE0000 <= cp <= 0xE007F else \
        "variation selector" if is_variation_selector(cp) else "noncharacter" if cp in NONCHARACTERS else \
        "line or paragraph separator" if cat in ("Zl", "Zp") else "unassigned code point" if cat == "Cn" else \
        "control character" if cat == "Cc" else "format character" if cat == "Cf" else "default-ignorable character" \
        if any(a <= cp <= b for a, b in DEFAULT_IGNORABLE) else "blank character"
    name = unicodedata.name(ch, "")
    return f"U+{cp:04X} ({kind}{', ' + name if name else ''})"


def escape(ch):
    """The Python escape for one character (in JSON, one above U+FFFF is a surrogate pair of \\u escapes)."""
    return f"\\u{ord(ch):04x}" if ord(ch) <= 0xFFFF else f"\\U{ord(ch):08x}"


def show(path):
    """A path safe to print: ascii() when it holds anything hidden or non-printable."""
    return path if path.isprintable() and not HIDDEN.search(path) else ascii(path)


def glob_rx(pattern):
    """Gitignore-style glob to regex: * and ? stay within one path segment, a ** segment spans zero or more
    directories, [abc] and [!abc] match one character other than /. Raises ConfigError for what it does not
    support: ** inside a segment, a POSIX class, / or [ inside a class, an invalid range."""
    if not isinstance(pattern, str) or not pattern:
        raise ConfigError(f"a glob must be a non-empty string: {pattern!r}")
    out, i, n = [], 0, len(pattern)
    while i < n:
        c = pattern[i]
        if pattern.startswith("**", i):
            if (i and pattern[i - 1] != "/") or (i + 2 < n and pattern[i + 2] != "/"):
                raise ConfigError(f"glob {pattern!r}: ** must be a whole path segment (a/**/b, **/x, a/**)")
            if i + 2 < n:
                out.append("(?:.*/)?")
                i += 3
            else:
                out.append(".*")
                i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        elif c == "[" and "]" in pattern[i + 2:]:
            j = pattern.index("]", i + 2)
            body = pattern[i + 1:j]
            neg = body[:1] in ("!", "^")
            body = body[1:] if neg else body
            if "[" in body or "/" in body:
                raise ConfigError(f"glob {pattern!r}: a class cannot hold [, / or a POSIX class like [:alpha:]")
            out.append(("[^/" if neg else "[") + body.replace("\\", "\\\\") + "]")
            i = j + 1
        else:
            out.append(re.escape(c))
            i += 1
    try:
        return re.compile("".join(out))
    except re.error as e:
        raise ConfigError(f"glob {pattern!r} is not valid: {e}")


def matcher(patterns):
    rxs = [glob_rx(p) for p in patterns]
    return lambda path: any(rx.fullmatch(path) for rx in rxs)


def read_bytes(full):
    """A regular file's bytes, or None for a symlink or a missing file."""
    if os.path.islink(full) or not os.path.isfile(full):
        return None
    with open(full, "rb") as f:
        return f.read()


def decode(data):
    """(text, valid): undecodable bytes are kept as surrogate escapes, so the rest can still be scanned."""
    try:
        return data.decode("utf-8"), True
    except UnicodeDecodeError:
        return data.decode("utf-8", "surrogateescape"), False


def binary_by_attr(root, files):
    """Paths .gitattributes marks as not text: -text, or the binary macro."""
    if not files:
        return set()
    r = subprocess.run(["git", "-C", root, "check-attr", "-z", "--stdin", "text", "binary"],
                       input=("\0".join(files) + "\0").encode(), capture_output=True, check=True)
    parts = r.stdout.decode("utf-8", "surrogateescape").split("\0")
    out = set()
    for k in range(0, len(parts) - 2, 3):
        path, attr, value = parts[k:k + 3]
        if (attr, value) in (("text", "unset"), ("binary", "set")):
            out.add(path)
    return out


def is_binary(data):
    """git's own test: a NUL byte in the first 8000 bytes."""
    return b"\0" in data[:8000]


# ---------------------------------------------------------------- config

def _globs(cfg, key, catch_all_ok=True):
    v = cfg[key]
    if not isinstance(v, list):
        raise ConfigError(f"{key} must be a list")
    out = []
    for item in v:
        if isinstance(item, str):
            g = item
        elif isinstance(item, dict) and isinstance(item.get("glob"), str) and isinstance(item.get("why"), str) \
                and set(k for k in item if not k.startswith("_")) <= {"glob", "why"}:
            g = item["glob"]
        else:
            raise ConfigError(f"{key} entries are a glob string or {{\"glob\": ..., \"why\": ...}}: {item!r}")
        glob_rx(g)
        if not catch_all_ok and set(g) <= set("*/"):
            raise ConfigError(f"{key}: {g!r} matches every file; list the paths that need it")
        out.append(g)
    return out


def _known(obj, keys, where):
    extra = sorted(k for k in obj if k not in keys and not k.startswith("_"))
    if extra:
        raise ConfigError(f"{where}: unknown key(s) {', '.join(extra)}")


def _regex(pattern, where, groups=0):
    if not isinstance(pattern, str):
        raise ConfigError(f"{where}: the pattern must be a string")
    try:
        rx = re.compile(pattern)
    except re.error as e:
        raise ConfigError(f"{where}: {pattern!r} is not a regex: {e}")
    if rx.groups < groups:
        raise ConfigError(f"{where}: {pattern!r} needs a group that captures the number")
    return rx


def _spec(c, key, required, optional=()):
    spec = c[key]
    where = f"claim {c['file']!r} {key}"
    if not isinstance(spec, dict):
        raise ConfigError(f"{where} must be an object with {', '.join(required)}")
    _known(spec, set(required) | set(optional), where)
    missing = [k for k in required if k not in spec]
    if missing:
        raise ConfigError(f"{where} is missing {', '.join(missing)}")
    for k, v in spec.items():
        if not k.startswith("_") and not isinstance(v, str):
            raise ConfigError(f"{where}: {k} must be a string")


def load_config(cfg):
    """Defaults filled in and every value checked. Keys starting with _ are comments, at any level."""
    if not isinstance(cfg, dict):
        raise ConfigError("the config must be a JSON object")
    _known(cfg, DEFAULTS, "config")
    cfg = {**DEFAULTS, **{k: v for k, v in cfg.items() if not k.startswith("_")}}
    for key in ("modes", "invisible", "stale", "stale_fails"):
        if not isinstance(cfg[key], bool):
            raise ConfigError(f"{key} must be true or false")
    if not isinstance(cfg["max_age_days"], int) or isinstance(cfg["max_age_days"], bool) or cfg["max_age_days"] < 0:
        raise ConfigError("max_age_days must be a whole number of days")
    cfg["invisible_allow"] = _globs(cfg, "invisible_allow", catch_all_ok=False)
    cfg["stale_globs"] = _globs(cfg, "stale_globs")
    cfg["stale_exclude"] = _globs(cfg, "stale_exclude", catch_all_ok=False)
    if not isinstance(cfg["stale_pattern"], str):
        raise ConfigError("stale_pattern must be a string")
    try:
        rx = re.compile(cfg["stale_pattern"], re.IGNORECASE)
    except re.error as e:
        raise ConfigError(f"stale_pattern is not a regex: {e}")
    if rx.groups < 1:
        raise ConfigError("stale_pattern needs a group that captures the YYYY-MM-DD date")
    for key in ("claims", "instructions", "root_safety"):
        if not isinstance(cfg[key], list):
            raise ConfigError(f"{key} must be a list")
    for c in cfg["claims"]:
        if not isinstance(c, dict):
            raise ConfigError(f"claims entries are objects: {c!r}")
        _known(c, CLAIM_KEYS, f"claim {c.get('file')!r}")
        counts = [k for k in ("count_glob", "count_json", "count_lines") if k in c]
        if not isinstance(c.get("file"), str) or not isinstance(c.get("pattern"), str) or len(counts) != 1:
            raise ConfigError(f"a claim needs file, pattern and exactly one of count_glob, count_json, count_lines: {c!r}")
        _regex(c["pattern"], f"claim {c['file']!r} pattern", groups=1)
        if "count_glob" in c:
            glob_rx(c["count_glob"])
        elif "count_json" in c:
            _spec(c, "count_json", ["file"], ["key"])
        else:
            _spec(c, "count_lines", ["file", "pattern"])
            _regex(c["count_lines"]["pattern"], f"claim {c['file']!r} count_lines")
    for item in cfg["instructions"]:
        if not isinstance(item, dict) or not isinstance(item.get("file"), str):
            raise ConfigError(f"instructions entries are objects with a file: {item!r}")
        _known(item, INSTRUCTION_KEYS, f"instructions {item['file']!r}")
        mb = item.get("max_bytes", 32768)
        if not isinstance(mb, int) or isinstance(mb, bool) or mb <= 0:
            raise ConfigError(f"instructions {item['file']!r}: max_bytes must be a positive whole number")
        if "sentinel" in item and (not isinstance(item["sentinel"], str) or not item["sentinel"].strip()
                                   or "\n" in item["sentinel"]):
            raise ConfigError(f"instructions {item['file']!r}: sentinel must be one non-empty line")
    if not all(isinstance(x, str) and x.strip() and "\n" not in x for x in cfg["root_safety"]):
        raise ConfigError("root_safety must be a list of one-line shell commands")
    return cfg


def loosened(old, new):
    """What new turns off or widens compared with old (both valid configs): notices, not failures."""
    old, new = load_config(old), load_config(new)
    out = []
    for key in ("modes", "invisible", "stale", "stale_fails"):
        if old[key] and not new[key]:
            out.append(f"turns {key} off")
    if new["max_age_days"] > old["max_age_days"]:
        out.append(f"raises max_age_days from {old['max_age_days']} to {new['max_age_days']}")
    for key in ("invisible_allow", "stale_exclude"):
        for g in new[key]:
            if g not in old[key]:
                out.append(f"adds {g!r} to {key}")
    for g in old["stale_globs"]:
        if g not in new["stale_globs"]:
            out.append(f"drops {g!r} from stale_globs")
    if new["stale_pattern"] != old["stale_pattern"]:
        out.append("changes stale_pattern")
    dump = lambda c: json.dumps({k: v for k, v in c.items() if not k.startswith("_")}, sort_keys=True)
    new_claims = {dump(c) for c in new["claims"]}
    for c in old["claims"]:
        if dump(c) not in new_claims:
            out.append(f"drops or changes a claim on {c['file']}")
    new_ins = {i["file"]: i for i in new["instructions"]}
    for i in old["instructions"]:
        n = new_ins.get(i["file"])
        if n is None:
            out.append(f"drops the instructions check on {i['file']}")
            continue
        if n.get("max_bytes", 32768) > i.get("max_bytes", 32768):
            out.append(f"raises max_bytes for {i['file']}")
        if i.get("sentinel") and n.get("sentinel") != i.get("sentinel"):
            out.append(f"drops or changes the sentinel for {i['file']}")
    for cmd in old["root_safety"]:
        if cmd not in new["root_safety"]:
            out.append(f"drops the root_safety command {cmd!r}")
    return out


def config_notices(root, rel, cfg, base):
    """Notices for a config that loosens the checks compared with the one at the merge base."""
    try:
        mb = git(root, "merge-base", base, "HEAD").strip()
    except subprocess.CalledProcessError:
        return []
    try:
        old = json.loads(git(root, "show", f"{mb}:{rel}"))
    except subprocess.CalledProcessError:
        return [f"config: {rel} is new in this change; review its allow-lists and exclusions"]
    except ValueError:
        return [f"config: {rel} at the base {mb[:12]} is not valid JSON; not compared"]
    try:
        return [f"config: this change to {rel} {x}; review it" for x in loosened(old, cfg)]
    except ConfigError:
        return [f"config: {rel} at the base {mb[:12]} is not a valid config; not compared"]


# ---------------------------------------------------------------- checks

def check_modes(root, base, out):
    if not base:
        return
    try:
        raw = git(root, "diff", "--raw", "-z", "-M", "--no-abbrev", f"{base}...HEAD")
    except subprocess.CalledProcessError as e:
        out["fail"].append(f"modes: cannot diff against {base}: {(e.stderr.strip().splitlines() or [''])[0]}")
        return
    parts = raw.split("\0")
    deleted, added = [], []  # 100755 files deleted, shebang files added as 100644: a rename git did not pair
    i = 0
    while i < len(parts) - 1:
        head = parts[i]
        if not head.startswith(":"):
            i += 1
            continue
        src_mode, dst_mode, _src, dst_sha, status = head[1:].split(" ")
        npaths = 2 if status[:1] in ("R", "C") else 1
        path = parts[i + npaths]
        i += 1 + npaths
        if status == "D" and src_mode == "100755":
            deleted.append(path)
            continue
        if dst_mode != "100644" or (src_mode != "100755" and status != "A"):
            continue
        if git(root, "cat-file", "blob", dst_sha, text=False)[:2] != b"#!":
            continue
        if status == "A":
            added.append(path)
        else:
            out["fail"].append(f"modes: {show(path)} lost its executable bit (100755 -> 100644); "
                               f"restore with: git update-index --chmod=+x {show(path)}")
    for path in added:
        for gone in deleted:
            if os.path.dirname(gone) == os.path.dirname(path) or os.path.basename(gone) == os.path.basename(path):
                out["fail"].append(f"modes: {show(path)} has a shebang and mode 100644, and {show(gone)} (100755) "
                                   f"was deleted in the same change: a rename that lost its executable bit? "
                                   f"restore with: git update-index --chmod=+x {show(path)}")
                break


def check_invisible(root, files, cfg, out):
    allowed = matcher(cfg["invisible_allow"])
    by_attr = binary_by_attr(root, files)
    for path in files:
        m = HIDDEN.search(path)
        if m:  # checked even when the file is allow-listed
            out["fail"].append(f"invisible: the path {show(path)} holds raw {describe(m.group())}; rename it")
        if allowed(path):
            continue
        full = os.path.join(root, path)
        if os.path.islink(full):
            m = HIDDEN.search(os.readlink(full))
            if m:
                out["fail"].append(f"invisible: the symlink {show(path)} points at a target holding raw {describe(m.group())}")
            continue
        data = read_bytes(full)
        if data is None or path in by_attr or is_binary(data):
            continue
        text, valid = decode(data)
        if not valid:
            out["fail"].append(f"invisible: {show(path)} is not valid UTF-8; convert it, or mark it binary in "
                               f".gitattributes if it is not text")
        for n, line in enumerate(text.split("\n"), 1):
            for m in HIDDEN_RUN.finditer(line):
                run_, col = m.group(), m.start()
                if n == 1 and col == 0 and run_[0] == BOM:
                    run_, col = run_[1:], 1
                    if not run_:
                        continue
                more = f" and {len(run_) - 1} more hidden character(s) after it" if len(run_) > 1 else ""
                out["fail"].append(f"invisible: {show(path)}:{n}:{col + 1} raw {describe(run_[0])}{more}; "
                                   f"write it as an escape ({escape(run_[0])} or an HTML entity)")
            for m in VS_RX.finditer(line):
                col = m.start()
                if not vs_ok(line[col - 1] if col else "", m.group()):
                    why = "an ideographic variation selector; if the file uses ideographic variation sequences, " \
                        "allow-list it" if ord(m.group()) >= 0xE0100 else "not after a character it is defined for"
                    out["fail"].append(f"invisible: {show(path)}:{n}:{col + 1} raw {describe(m.group())}, {why}; "
                                       f"write it as an escape ({escape(m.group())})")


def count_for(root, files, claim):
    if "count_glob" in claim:
        match = matcher([claim["count_glob"]])
        return sum(1 for p in files if match(p))
    if "count_json" in claim:  # {"file": ..., "key": "a.b"} -> len(value at that key)
        spec = claim["count_json"]
        with open(os.path.join(root, spec["file"]), encoding="utf-8") as f:
            v = json.load(f)
        for k in filter(None, spec.get("key", "").split(".")):
            v = v[k]
        return len(v)
    spec = claim["count_lines"]  # {"file": ..., "pattern": regex} -> lines that match
    rx = re.compile(spec["pattern"])
    with open(os.path.join(root, spec["file"]), encoding="utf-8") as f:
        return sum(1 for line in f if rx.search(line))


NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+|\d+")


def check_claims(root, files, cfg, out):
    for claim in cfg["claims"]:
        where = f"claims: {claim['file']}"
        try:
            with open(os.path.join(root, claim["file"]), encoding="utf-8") as f:
                text = f.read()
            actual = count_for(root, files, claim)
        except (OSError, ValueError, KeyError, TypeError, IndexError, re.error) as e:
            out["fail"].append(f"{where}: cannot check {claim['pattern']!r}: {type(e).__name__}: {e}")
            continue
        found = [m.group(1) for m in re.finditer(claim["pattern"], text)]
        if not found:
            out["fail"].append(f"{where}: pattern {claim['pattern']!r} not found")
            continue
        for stated in found:
            if stated is None or not NUMBER.fullmatch(stated):
                out["fail"].append(f"{where}: pattern {claim['pattern']!r} matched, but its group 1 captured "
                                   f"{stated!r}, not a number; fix the pattern")
            elif int(stated.replace(",", "")) != actual:
                out["fail"].append(f"{where} states {stated} for {claim['pattern']!r}; the repo has {actual}")


FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")


def check_stale(root, files, cfg, out, today):
    rx = re.compile(cfg["stale_pattern"], re.IGNORECASE)
    wanted, excluded = matcher(cfg["stale_globs"]), matcher(cfg["stale_exclude"])
    limit = cfg["max_age_days"]
    bucket = "fail" if cfg["stale_fails"] else "warn"
    for path in files:
        if not wanted(path) or excluded(path):
            continue
        data = read_bytes(os.path.join(root, path))
        if data is None or is_binary(data):
            continue
        text = decode(data)[0]
        fence = None  # the opening fence while inside a fenced code block
        old = []  # (date, line) of each stale marker; one message per file
        for n, line in enumerate(text.split("\n"), 1):
            f = FENCE.match(line)
            if fence is None and f:
                fence = f.group(1)
                continue
            if fence is not None:
                if f and f.group(1)[0] == fence[0] and len(f.group(1)) >= len(fence) \
                        and not line[f.end():].strip():
                    fence = None
                continue
            for m in rx.finditer(line):
                try:
                    when = dt.date.fromisoformat(m.group(1))
                except (ValueError, TypeError):
                    continue
                if (today - when).days > limit:
                    old.append((when, n))
        if old:
            when, n = min(old)
            out[bucket].append(f"stale: {show(path)}:{n} {len(old)} dated marker(s) older than {limit} days; "
                               f"oldest {when} ({(today - when).days} days ago). Recheck and redate, or drop the date")


def check_instructions(root, cfg, out):
    for item in cfg["instructions"]:
        path = os.path.join(root, item["file"])
        if os.path.islink(path) or not os.path.isfile(path):
            out["fail"].append(f"instructions: {item['file']} is missing (or a symlink)")
            continue
        size = os.path.getsize(path)
        limit = item.get("max_bytes", 32768)
        if size > limit:
            out["fail"].append(f"instructions: {item['file']} is {size} bytes, over its limit of {limit}")
        sentinel = item.get("sentinel")
        if sentinel:
            text = decode(read_bytes(path))[0]
            if text.startswith(BOM):
                text = text[1:]
            lines = [l for l in text.split("\n") if l.strip()]
            if not lines or lines[-1].strip() != sentinel.strip():
                out["fail"].append(f"instructions: {item['file']} must end with the sentinel line {sentinel!r}")


def run(root, cfg, base, today=None):
    cfg = load_config(cfg)
    out = {"fail": [], "warn": []}
    files = tracked(root)
    for key in ("invisible_allow", "stale_exclude"):
        for g in cfg[key]:
            match = matcher([g])
            if len(files) > 1 and all(match(p) for p in files):
                raise ConfigError(f"{key}: {g!r} matches every tracked file; list the paths that need it")
    if cfg["modes"]:
        check_modes(root, base, out)
    if cfg["invisible"]:
        check_invisible(root, files, cfg, out)
    check_claims(root, files, cfg, out)
    if cfg["stale"]:
        check_stale(root, files, cfg, out, today or dt.date.today())
    check_instructions(root, cfg, out)
    return out


# ---------------------------------------------------------------- selftest

def selftest():
    """Every check against a planted defect in a temp git repo. No network, no user or system git config."""
    ok = True

    def expect(name, cond):
        nonlocal ok
        print(("PASS  " if cond else "FAIL  ") + name)
        ok &= bool(cond)

    def fails(r, *needles):
        return any(all(s in x for s in needles) for x in r["fail"])

    with tempfile.TemporaryDirectory() as d:
        os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", HOME=d,
                          GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                          GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
        repo = os.path.join(d, "repo")
        os.mkdir(repo)

        def sh(*a):
            subprocess.run(["git", "-C", repo, "-c", "commit.gpgsign=false", *a], check=True, capture_output=True)

        def put(rel, text, mode=0o644):
            full = os.path.join(repo, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            os.chmod(full, mode)

        sh("init", "-q")
        sh("config", "core.fileMode", "true")
        for s in "ab":
            put(f"skills/{s}/SKILL.md", "x\n")
        put("skills/a/nested/SKILL.md", "not a skill dir\n")
        put("run.sh", "#!/bin/sh\necho hi\n", 0o755)
        put("old name.sh", "#!/bin/sh\necho renamed\n", 0o755)
        put("data.txt", "no shebang\n", 0o755)
        put("README.md", "Two skills: 2 skills.\nchecked 2026-01-01\n\tTabs, CRLF\r\n and a BOM later are fine.\n")
        put("bom.txt", BOM + "a file that starts with a BOM\n")
        put("AGENTS.md", "rules\nSentinel: end\n\n")
        put("fixtures/trap.json", '{"t": "\u202e"}\n')
        sh("add", "-A")
        sh("commit", "-qm", "base")
        cfg = {"_comment": "keys starting with _ are comments",
               "claims": [{"file": "README.md", "pattern": r"(\d+) skills", "count_glob": "skills/*/SKILL.md"}],
               "instructions": [{"file": "AGENTS.md", "max_bytes": 100, "sentinel": "Sentinel: end"}],
               "invisible_allow": [{"glob": "fixtures/**", "why": "planted on purpose"}]}
        today = dt.date(2026, 1, 20)
        r = run(repo, cfg, "HEAD", today)
        expect("clean repo: no failures, no warnings (BOM at start, tabs, CR, allow-listed fixture)",
               r == {"fail": [], "warn": []})
        expect("count_glob * stays in one directory", not fails(r, "claims"))

        sh("mv", "old name.sh", "new name.sh")
        for name in ("run.sh", "data.txt", "new name.sh"):
            os.chmod(os.path.join(repo, name), 0o644)
        put("README.md", "Now 3 skills.\nchecked 2025-10-01\n```\nchecked 2020-01-01 in a fence\n```\n"
                         "~~~~\n```\nchecked 2020-02-02 still fenced\n~~~~\nverified: 2025-09-09\n")
        put("x.py", "s = 'admin\u202e'  # bidi\nt = '1\u200b2'\nu = '\x1b[31m'\nv = 'tag\U000e0041\U000e0042\U000e0043'\n"
                    "w = 'soft\u00adhyphen'\nz = 'late \ufeff BOM'\n")
        put("bad\u200bname.txt", "x\n")
        put("AGENTS.md", "Sentinel: end\nappended after the sentinel\n")
        sh("add", "-A")
        sh("commit", "-qm", "bad")
        r = run(repo, cfg, "HEAD~1", today)
        expect("lost executable bit is caught", fails(r, "run.sh lost its executable bit"))
        expect("lost executable bit is caught through a rename and a space", fails(r, "new name.sh lost"))
        expect("a mode change on a file without a shebang is ignored", not fails(r, "data.txt"))
        expect("bidi control is caught", fails(r, "x.py:1:", "U+202E", "bidi"))
        expect("zero-width space is caught", fails(r, "x.py:2:", "U+200B"))
        expect("ESC control character is caught", fails(r, "x.py:3:", "U+001B"))
        expect("tag-block character is caught, with a long escape", fails(r, "x.py:4:", "U+E0041", "tag", "\\U000e0041"))
        expect("a run of hidden characters is one message", fails(r, "x.py:4:", "and 2 more hidden character(s)")
               and sum(x.startswith("invisible: x.py:4:") for x in r["fail"]) == 1)
        expect("soft hyphen (Cf) is caught", fails(r, "x.py:5:", "U+00AD"))
        expect("a BOM after the start of the file is caught", fails(r, "x.py:6:", "U+FEFF"))
        expect("a hidden character in a path is caught and printed escaped",
               fails(r, "the path 'bad\\u200bname.txt'"))
        expect("no message holds a raw hidden character", not any(HIDDEN.search(x) for x in r["fail"]))
        expect("README count drift is caught", fails(r, "states 3", "has 2"))
        expect("sentinel not last is caught", fails(r, "must end with the sentinel"))
        warned = "\n".join(r["warn"])
        expect("stale date warns, does not fail", "README.md:" in warned and not fails(r, "stale"))
        expect("dates inside ``` and ~~~~ fences are skipped", "2020-" not in warned)
        expect("the line after a fence is checked again; one message per file, oldest first",
               len(r["warn"]) == 1 and "README.md:10 2 dated marker(s)" in warned and "oldest 2025-09-09" in warned)
        r = run(repo, {**cfg, "stale_fails": True}, "HEAD~1", today)
        expect("stale_fails turns the warning into a failure", fails(r, "stale: README.md:10 "))
        r = run(repo, {**cfg, "stale_pattern": r"reviewed (\d{4}-\d{2}-\d{2})"}, "HEAD~1", today)
        expect("a custom stale_pattern replaces the default", not r["warn"])
        r = run(repo, {**cfg, "stale_exclude": ["README.md"]}, "HEAD~1", today)
        expect("stale_exclude skips a file", not r["warn"])
        r = run(repo, cfg, "HEAD~1", dt.date(2025, 9, 1))
        expect("a date in the future is not stale", not r["warn"])
        r = run(repo, {**cfg, "invisible_allow": ["x.py"]}, "HEAD~1", today)
        expect("invisible_allow skips a listed file", not fails(r, "x.py"))
        expect("globs: [!a] never matches /", not glob_rx("[!a]").fullmatch("/"))
        expect("globs: a/**/b matches a/b and a/x/y/b", glob_rx("a/**/b").fullmatch("a/b")
               and glob_rx("a/**/b").fullmatch("a/x/y/b") and not glob_rx("a/**/b").fullmatch("ab"))
        r = run(repo, {**cfg, "invisible_allow": ["*.py"]}, "HEAD~1", today)
        expect("globs: *.py matches only at the top level", not fails(r, "x.py"))
        r = run(repo, {**cfg, "invisible_allow": []}, "HEAD~1", today)
        expect("without its allow-list entry the fixture is caught", fails(r, "fixtures/trap.json:1:"))
        r = run(repo, {**cfg, "modes": False, "invisible": False}, "HEAD~1", today)
        expect("modes and invisible can be turned off", not fails(r, "modes:") and not fails(r, "invisible:"))
        big = {**cfg, "instructions": [{"file": "AGENTS.md", "max_bytes": 5}]}
        expect("byte limit is enforced", fails(run(repo, big, None, today), "over its limit of 5"))
        r = run(repo, {**cfg, "instructions": [{"file": "MISSING.md"}]}, None, today)
        expect("a missing instruction file fails", fails(r, "MISSING.md is missing"))
        r = run(repo, {**cfg, "claims": [{"file": "NOPE.md", "pattern": r"(\d+)", "count_glob": "*"}]}, None, today)
        expect("a claim on a missing file fails instead of crashing", fails(r, "NOPE.md: cannot check"))
        r = run(repo, {**cfg, "claims": [{"file": "README.md", "pattern": r"(\d+) skills",
                                          "count_lines": {"file": "x.py", "pattern": r"^\w ="}}]}, None, today)
        expect("count_lines counts matching lines", fails(r, "states 3", "has 6"))
        r = run(repo, {**cfg, "claims": [{"file": "README.md", "pattern": r"(\d+) widgets", "count_glob": "*"}]},
                None, today)
        expect("a claim whose pattern is not found fails", fails(r, "pattern '(\\\\d+) widgets' not found"))
        r = run(repo, {**cfg, "claims": [{"file": "README.md", "pattern": r"(\d+)?checked", "count_glob": "*"}]},
                None, today)
        expect("a claim group that did not take part fails cleanly", fails(r, "captured None, not a number"))
        r = run(repo, {**cfg, "claims": [{"file": "README.md", "pattern": r"(\w+) 3 skills", "count_glob": "*"}]},
                None, today)
        expect("a claim group that captured a word fails cleanly", fails(r, "captured 'Now', not a number"))

        # second round: binary detection, the wider invisible set, variation selectors, symlinks, renames
        sh("mv", "run.sh", "gone.sh")
        sh("commit", "-qm", "rename")
        put("tools/big.sh", "#!/bin/sh\n" + "".join(f"echo line {k}\n" for k in range(60)), 0o755)
        sh("add", "-A")
        sh("commit", "-qm", "big")
        sh("rm", "-q", "tools/big.sh")
        put("tools/big3.sh", "#!/bin/sh\necho rewritten\n")
        with open(os.path.join(repo, "late-nul.sh"), "wb") as f:
            f.write(b"#!/bin/sh\necho \"\xe2\x80\xae\"\n" + b"#" * 9000 + b"\0\n")
        with open(os.path.join(repo, "early-nul.bin"), "wb") as f:
            f.write(b"\0\xe2\x80\xae binary\n")
        with open(os.path.join(repo, "latin.md"), "wb") as f:
            f.write(b"caf\xe9 \x1b[2J\n")
        put(".gitattributes", "*.dat binary\nraw.txt -text\n")
        put("marked.dat", "x\U0000202ey\n")
        put("raw.txt", "x\U0000202ey\n")
        put("y.txt", "a\U00003164b\nc\U00002800d\ne\U0000034ff\ng\x1ch\ni\x85j\nform\x0cfeed\x0bvtab\n"
                     "heart \U00002764\U0000FE0F keycap 1\U0000FE0F\U000020E3 flag \U0001F3F3\U0000FE0F serif "
                     "\U00002229\U0000FE00 myanmar \U00001000\U0000FE00 new emoji \U0001FAE9 \U0001FAC6\n"
                     "bare a\U0000FE0F and a\U000E0100 and twice \U00002764\U0000FE0F\U0000FE0F\n"
                     "ascii =\U0000FE06= +\U0000FE0F keycap text 1\U0000FE0E arrow \U00002192\U0000FE0F cjk \U00004E00\U0000FE00 ivs \U00004E00\U000E0100\n"
                     "smuggled \U000E0263\U000E0275 nonchar \U0000FDD0 last \U0010FFFF reserved \U00002065 \U0000FFF0 "
                     "assigned later \U00000378\n"
                     "// check the user is admin\U00002028isAdmin = true; para\U00002029graph\n")
        os.symlink("tgt\U0000200b", os.path.join(repo, "fixtures", "link"))
        put("fixtures/odd\U00002066name.txt", "x\n")
        put("ONE.md", BOM + "Sentinel: end\n")
        sh("add", "-A")
        sh("commit", "-qm", "round2")
        r = run(repo, {**cfg, "instructions": [{"file": "ONE.md", "sentinel": "Sentinel: end"}]}, "HEAD~1", today)
        expect("a deleted 100755 script and an added 100644 one beside it are a lost bit (rename plus rewrite)",
               fails(r, "tools/big3.sh has a shebang and mode 100644", "tools/big.sh (100755) was deleted"))
        r2 = run(repo, cfg, "HEAD~2", today)
        expect("a plain rename that keeps the bit is not flagged", not fails(r2, "gone.sh"))
        expect("a NUL after the first 8000 bytes is text and is scanned", fails(r, "late-nul.sh:2:", "U+202E"))
        expect("a NUL in the first 8000 bytes is binary and skipped", not fails(r, "early-nul.bin"))
        expect("a file that is not UTF-8 fails", fails(r, "latin.md is not valid UTF-8"))
        expect("a file that is not UTF-8 is still scanned", fails(r, "latin.md:1:", "U+001B"))
        expect("the binary attribute and -text skip a file", not fails(r, "marked.dat") and not fails(r, "raw.txt"))
        for line, cp in ((1, "U+3164"), (2, "U+2800"), (3, "U+034F"), (4, "U+001C"), (5, "U+0085")):
            expect(f"{cp} is caught", fails(r, f"y.txt:{line}:", cp))
        expect("form feed and vertical tab are whitespace", not fails(r, "y.txt:6:"))
        expect("variation selectors in emoji and standardized sequences pass, and so do code points newer than "
               "this Python's Unicode tables", not fails(r, "y.txt:7:"))
        expect("a variation selector after a letter is caught", fails(r, "y.txt:8:7 ", "U+FE0F"))
        expect("an ideographic variation selector after a letter is caught", fails(r, "y.txt:8:14 ", "U+E0100"))
        expect("a second variation selector in a row is caught", fails(r, "y.txt:8:", "U+FE0F")
               and sum(x.startswith("invisible: y.txt:8:") for x in r["fail"]) == 3)
        for col, cp, why in ((8, "U+FE06", "after an ASCII symbol"), (12, "U+FE0F", "after ASCII + (category Sm)"),
                             (27, "U+FE0E", "text style after a keycap base"),
                             (36, "U+FE0F", "after a symbol not in emoji-variation-sequences")):
            expect(f"a variation selector {why} is caught", fails(r, f"y.txt:9:{col} ", cp))
        expect("U+FE00 after an ideograph with no standardized variant is caught", fails(r, "y.txt:9:43 ", "U+FE00"))
        expect("an ideographic variation selector is caught even after an ideograph", fails(r, "y.txt:9:", "U+E0100"))
        expect("the block after the tags (U+E0263, default-ignorable and unassigned) is caught",
               fails(r, "y.txt:10:10 ", "U+E0263", "and 1 more"))
        expect("a noncharacter is caught", fails(r, "y.txt:10:", "U+FDD0"))
        expect("the last noncharacter of plane 16 is caught", fails(r, "y.txt:10:", "U+10FFFF", "noncharacter"))
        expect("reserved default-ignorables U+2065 and U+FFF0 are caught",
               fails(r, "y.txt:10:", "U+2065") and fails(r, "y.txt:10:", "U+FFF0"))
        expect("an unassigned code point outside those ranges is not flagged", not fails(r, "y.txt:10:", "U+0378"))
        expect("U+2028 (ends a line in JavaScript) and U+2029 are caught",
               fails(r, "y.txt:11:", "U+2028", "separator") and fails(r, "y.txt:11:", "U+2029"))
        expect("an allow-listed symlink is skipped",
               not fails(r, "fixtures/link"))
        r3 = run(repo, {**cfg, "invisible_allow": []}, "HEAD~1", today)
        expect("a symlink whose target holds a hidden character is caught", fails(r3, "the symlink fixtures/link"))
        expect("a path name is checked even when the file is allow-listed", fails(r, "the path 'fixtures/odd\\u2066name.txt'"))
        expect("a BOM before a one-line sentinel file is allowed", not fails(r, "ONE.md"))

        expect("loosening: identical configs give no notices", loosened(cfg, cfg) == [])
        notes = loosened(cfg, {**cfg, "invisible": False, "invisible_allow": ["fixtures/**", "src/x.py"],
                               "instructions": [], "max_age_days": 90})
        expect("loosening: turning a check off, widening an allow-list, dropping instructions, a longer age",
               any("turns invisible off" in x for x in notes) and any("'src/x.py'" in x for x in notes)
               and any("drops the instructions check on AGENTS.md" in x for x in notes)
               and any("max_age_days from 45 to 90" in x for x in notes))
        expect("loosening: tightening gives no notices", loosened(cfg, {**cfg, "stale_fails": True}) == [])
        r = run(repo, cfg, "no-such-ref", today)
        expect("an unknown --base fails", fails(r, "cannot diff against no-such-ref"))
        for bad, why in (({"stale_globz": []}, "unknown key"), ({"stale_pattern": "no group"}, "needs a group"),
                         ({"invisible_allow": [{"glob": "x"}]}, "glob"), ({"root_safety": ["a\nb"]}, "one-line"),
                         ({"claims": [{"file": "a", "pattern": "(1)"}]}, "exactly one"),
                         ({"max_age_days": "45"}, "whole number"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_glob": "*", "typo": 1}]}, "unknown key(s) typo"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_json": {"file": "d", "kye": "a"}}]},
                          "unknown key(s) kye"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_json": "d.json"}]}, "must be an object"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_json": {"file": 3}}]}, "must be a string"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_lines": {"file": "d", "patern": "x"}}]},
                          "unknown key(s) patern"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_lines": {"file": "d", "pattern": "("}}]},
                          "is not a regex"),
                         ({"invisible_allow": ["[z-a]"]}, "is not valid"), ({"stale_globs": ["[[:alpha:]]"]}, "POSIX"),
                         ({"stale_globs": ["docs**.md"]}, "whole path segment"),
                         ({"invisible_allow": ["**"]}, "matches every file"),
                         ({"invisible_allow": ["**/*"]}, "matches every file"),
                         ({"stale_exclude": ["*"]}, "matches every file"),
                         ({"invisible_allow": ["**/?*"]}, "matches every tracked file"),
                         ({"stale_exclude": [{"glob": "a**", "why": "x"}]}, "whole path segment"),
                         ({"stale_exclude": ["?*", "**/?*"]}, "matches every tracked file"),
                         ({"claims": {"file": "a"}}, "claims must be a list"),
                         ({"instructions": ["AGENTS.md"]}, "objects with a file"),
                         ({"stale_pattern": 5}, "must be a string")):
            try:
                run(repo, bad, None, today)
                expect(f"config error: {why}", False)
            except ConfigError as e:
                expect(f"config error: {why}", why in str(e))
    print("all checks hold" if ok else "SELFTEST FAILED")
    return 0 if ok else 1


# ---------------------------------------------------------------- main

def annotate(level, msg):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        msg = msg.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        return f"::{level}::{msg}"
    return f"{ {'error': 'FAIL', 'warning': 'WARN'}.get(level, 'NOTE')}  {msg}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--config", help="config path relative to --root (default .hygiene.json, optional)")
    ap.add_argument("--base", help="git ref to compare modes and the config against (a PR's base commit)")
    ap.add_argument("--today", type=dt.date.fromisoformat, help="date for the stale check, YYYY-MM-DD")
    ap.add_argument("--print-root-safety", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    cfg_path = os.path.join(a.root, a.config or ".hygiene.json")
    cfg = {}
    try:
        if os.path.isfile(cfg_path):
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
        elif a.config:
            raise ConfigError(f"{cfg_path} does not exist")
        if a.print_root_safety:
            for cmd in load_config(cfg)["root_safety"]:
                print(cmd)
            return 0
        r = run(a.root, cfg, a.base, a.today)
        notices = config_notices(a.root, a.config or ".hygiene.json", cfg, a.base) if a.base else []
    except (ConfigError, ValueError) as e:
        print(annotate("error", f"config {cfg_path}: {e}"))
        return 2
    for x in notices:
        print(annotate("notice", x))
    for w in r["warn"]:
        print(annotate("warning", w))
    for x in r["fail"]:
        print(annotate("error", x))
    print(f"{len(r['fail'])} failure(s), {len(r['warn'])} warning(s)")
    return 1 if r["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
