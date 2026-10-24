#!/usr/bin/env python3
"""根据 music.json 自动从网易云下载歌词。

用法（在项目根目录执行）：
    python tools/fetch-lrc.py

脚本会：
  1. 读取 server/assets/music.json 里的歌单
  2. 用歌名 + 歌手搜索网易云，找到歌曲 ID
  3. 下载 LRC 歌词（原版 + 翻译合并）
  4. 保存到 public/music/<slug>/<slug>.lrc
  5. 更新 music.json 标记 lrc: true

已经下载过歌词的歌会跳过，避免覆盖。要重新下载，先删掉对应的 .lrc 文件。
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUSIC_JSON = ROOT / "server" / "assets" / "music.json"
PUBLIC_MUSIC = ROOT / "public" / "music"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://music.163.com/",
}


def api_request(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _is_exclude_version(name: str) -> bool:
    """判断是否 Live / Remix / TV size 等特殊版本。"""
    lower = name.lower()
    return any(key in lower for key in _EXCLUDE_VERSIONS)


def search_song(name: str, artist: str) -> int | None:
    """搜索歌曲，返回最匹配的网易云歌曲 ID。优先录音室版，排除 Live / Remix 等。"""
    query = urllib.parse.quote(f"{name} {artist}")
    url = (
        "https://music.163.com/api/search/get/web"
        f"?s={query}&type=1&offset=0&total=true&limit=20"
    )
    data = api_request(url)

    if data.get("code") != 200:
        return None

    songs = data.get("result", {}).get("songs", [])
    if not songs:
        return None

    name_lower = name.lower()
    artist_lower = artist.lower()

    # 去掉括号后缀后的干净歌名
    def _clean(s: str) -> str:
        return re.sub(r"\s*[\(\（].*?[\)\）]", "", s).lower().strip()

    clean_name = _clean(name)

    # 第一轮：完全匹配（去括号后）+ 歌手匹配 + 非特殊版本
    for song in songs:
        s_name = song.get("name", "")
        if _is_exclude_version(s_name):
            continue
        s_artists = [a.get("name", "").lower() for a in song.get("artists", [])]
        if _clean(s_name) == clean_name:
            if any(artist_lower in sa for sa in s_artists):
                return song.get("id")

    # 第二轮：歌名包含关系 + 歌手匹配 + 非特殊版本
    for song in songs:
        s_name = song.get("name", "")
        if _is_exclude_version(s_name):
            continue
        s_artists = [a.get("name", "").lower() for a in song.get("artists", [])]
        if name_lower in s_name.lower() or clean_name in _clean(s_name):
            if any(artist_lower in sa for sa in s_artists):
                return song.get("id")

    # 第三轮：完全匹配（去括号后），不管版本类型
    for song in songs:
        s_name = song.get("name", "")
        s_artists = [a.get("name", "").lower() for a in song.get("artists", [])]
        if _clean(s_name) == clean_name:
            if any(artist_lower in sa for sa in s_artists):
                return song.get("id")

    # 第四轮：歌名包含关系
    for song in songs:
        s_name = song.get("name", "")
        if name_lower in s_name.lower() or _clean(s_name) == clean_name:
            return song.get("id")

    # 最后返回第一个结果
    return songs[0].get("id")


def fetch_lyric(song_id: int) -> tuple[str, str]:
    """获取歌词，返回 (原版, 翻译)。"""
    url = f"https://music.163.com/api/song/lyric?id={song_id}&lv=1&kv=1&tv=-1"
    data = api_request(url)

    lrc = ""
    tlyric = ""

    if data.get("lrc") and data["lrc"].get("lyric"):
        lrc = data["lrc"]["lyric"]
    if data.get("tlyric") and data["tlyric"].get("lyric"):
        tlyric = data["tlyric"]["lyric"]

    return lrc, tlyric


def parse_lrc_lines(text: str) -> dict[str, str]:
    """把 LRC 文本解析成 {时间戳: 内容}。"""
    lines: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # [mm:ss.xx]内容
        m = re.match(r"^(\[\d{1,3}:\d{2}\.\d{2,3}\])(.*)$", line)
        if m:
            ts, content = m.group(1), m.group(2).strip()
            lines[ts] = content
    return lines


# 作词/作曲/编曲等元数据行要过滤掉
_META_RE = re.compile(
    r"^(作词|作曲|编曲|制作人|监制|编舞|出品|发行|OP|SP|录音|混音|母带|"
    r"吉他|贝斯|鼓|键盘|弦乐|和声|封面|文案|策划|导演|摄影|美术|设计|"
    r"A&R|经纪|版权|出品人|唱片|公司|工作室|填词|谱曲|原唱|翻唱|改编|"
    r"Remix|Ver\.|Version|Mix|Master|Guitar|Bass|Drum|Keyboard|Piano|"
    r"Violin|Strings|Chorus|Backing|Vocal|Producer|Arranger|Composer|"
    r"Lyricist|Engineer|Studio|Label|Publisher|Copyright|Cover|Art|"
    r"Design|Photo|Director)\s*[:：]"
)

# 排除 Live / Remix / TV size 等版本的关键词
_EXCLUDE_VERSIONS = {
    "live", "remix", "tv size", "tvsize", "instrumental", "acoustic",
    "off vocal", "karaoke", "cover", "ver.", "version", "edit",
    "short", "clip", "demo", "take", "session",
}


def is_meta_line(content: str) -> bool:
    """判断一行歌词是否是作词/作曲等元数据。"""
    return bool(_META_RE.match(content.strip()))


def merge_lrc(lrc: str, tlyric: str) -> str:
    """把原版和翻译合并成项目支持的格式（翻译行带 [tr] 标记），过滤元数据行。"""
    original = parse_lrc_lines(lrc)
    translation = parse_lrc_lines(tlyric) if tlyric else {}

    # 保留原版的顺序
    result_lines: list[str] = []
    for line in lrc.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(\[\d{1,3}:\d{2}\.\d{2,3}\])(.*)$", line)
        if not m:
            result_lines.append(line)
            continue
        ts, content = m.group(1), m.group(2).strip()
        if is_meta_line(content):
            continue
        result_lines.append(f"{ts}{content}")
        # 如果有对应翻译，加一行 [tr] 版本
        tr = translation.get(ts, "").strip()
        if tr and tr != content and not is_meta_line(tr):
            result_lines.append(f"{ts}[tr]{tr}")

    return "\n".join(result_lines) + "\n"


def main() -> int:
    if not MUSIC_JSON.exists():
        print(f"! 找不到 {MUSIC_JSON}")
        return 1

    with open(MUSIC_JSON, "r", encoding="utf-8") as f:
        playlist = json.load(f)

    songs = playlist.get("songs", [])
    if not songs:
        print("歌单为空，没什么可下载的。")
        return 0

    updated = False

    for song in songs:
        name = song.get("name", "")
        artist = song.get("artist", "")
        slug = song.get("slug", "")

        if not slug:
            print(f"! {name} 没有 slug，跳过")
            continue

        dest = PUBLIC_MUSIC / slug / f"{slug}.lrc"

        # 已有歌词且 music.json 已标记 → 跳过
        if dest.exists() and song.get("lrc"):
            print(f"✓ {name} — 已有歌词，跳过")
            continue

        print(f"\n🎵 {name} — {artist}")

        song_id = search_song(name, artist)
        if not song_id:
            print(f"  ! 搜索不到这首歌")
            continue

        print(f"  歌曲 ID: {song_id}")

        try:
            lrc_text, tlyric_text = fetch_lyric(song_id)
        except urllib.error.HTTPError as e:
            print(f"  ! 获取歌词失败: HTTP {e.code}")
            continue
        except Exception as e:
            print(f"  ! 获取歌词失败: {e}")
            continue

        if not lrc_text or lrc_text.strip() == "":
            print(f"  ! 这首歌没有歌词")
            continue

        # 纯音乐标记
        if "纯音乐" in lrc_text and len(lrc_text) < 200:
            print(f"  ! 纯音乐，无歌词")
            continue

        merged = merge_lrc(lrc_text, tlyric_text)

        # 检查过滤后是否还有有效歌词
        lyric_lines = [l for l in merged.splitlines() if l.strip() and not l.strip().startswith("[")]
        if not lyric_lines:
            print(f"  ! 过滤元数据后歌词为空")
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(merged, encoding="utf-8")
        print(f"  ✓ 已保存: {dest.relative_to(ROOT)}")

        song["lrc"] = True
        updated = True

    if updated:
        with open(MUSIC_JSON, "w", encoding="utf-8") as f:
            json.dump(playlist, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"\n📋 已更新 {MUSIC_JSON.relative_to(ROOT)}")
        print("下一步：刷新页面即可看到歌词")
    else:
        print("\n没有新歌词需要下载。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
