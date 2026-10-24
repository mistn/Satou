#!/usr/bin/env python3
"""把一堆音频文件整理成站点能直接播放的目录结构。

用法（在项目根目录执行）：
    pip install mutagen pypinyin     # 首次使用装一次
    python tools/music-prep.py                 # 扫描 music-inbox/，整理进 public/music/
    python tools/music-prep.py --list          # 只预览，不写任何文件
    python tools/music-prep.py --inbox D:/歌   # 指定别的来源目录
    python tools/music-prep.py --reset         # 忽略已有歌单，全部重新生成

脚本做四件事：
  1. 读每首歌的 ID3 / FLAC / MP4 标签，拿到歌名和歌手
  2. 生成 ASCII slug（中文转拼音、日文假名转罗马字），保证 URL 干净
  3. 复制音频到 public/music/<slug>/<slug>.<ext>，并把内嵌封面转成 512×512 webp
  4. 重写 server/assets/music.json

同名歌曲重复跑是安全的：已有 slug 会被保留，不会因为改了标签就换 URL。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_MUSIC = ROOT / "public" / "music"
MUSIC_JSON = ROOT / "server" / "assets" / "music.json"
# 音频自带封面和同名图片都没有时，用站点头像兜底
DEFAULT_COVER = ROOT / "public" / "avatar.jpg"

AUDIO_EXT = {".mp3", ".flac", ".m4a", ".wav", ".ogg", ".opus"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}

# --- 假名 → 罗马字（片假名会先折算成平假名再查表）---------------------------
_KANA_ROWS = [
    ("あいうえお", "a i u e o"),
    ("かきくけこ", "ka ki ku ke ko"),
    ("がぎぐげご", "ga gi gu ge go"),
    ("さしすせそ", "sa shi su se so"),
    ("ざじずぜぞ", "za ji zu ze zo"),
    ("たちつてと", "ta chi tsu te to"),
    ("だぢづでど", "da ji zu de do"),
    ("なにぬねの", "na ni nu ne no"),
    ("はひふへほ", "ha hi fu he ho"),
    ("ばびぶべぼ", "ba bi bu be bo"),
    ("ぱぴぷぺぽ", "pa pi pu pe po"),
    ("まみむめも", "ma mi mu me mo"),
    ("やゆよ", "ya yu yo"),
    ("らりるれろ", "ra ri ru re ro"),
    ("わをん", "wa wo n"),
    ("ゃゅょ", "ya yu yo"),
    ("ぁぃぅぇぉ", "a i u e o"),
]

KANA = {}
for _row, _roman in _KANA_ROWS:
    for _ch, _r in zip(_row, _roman.split()):
        KANA[_ch] = _r
KANA["ー"] = "-"
KANA["ゔ"] = "vu"

_KANA_RE = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]+")


def kana_to_romaji(text: str) -> str:
    out = []
    for ch in text:
        code = ord(ch)
        # 片假名区 ァ(30A1) - ヶ(30F6) 折算到平假名
        if 0x30A1 <= code <= 0x30F6:
            ch = chr(code - 0x60)
        out.append(KANA.get(ch, ch))
    return " ".join(out)


def romanize(text: str) -> str:
    """按原顺序把混排的中日文转成罗马字。

    假名走本地映射表，其余段落整段交给 pypinyin —— 整段转换能保住词语上下文，
    逐字转会把「音楽」这类多音字读错。
    """
    try:
        import pypinyin
    except ImportError:
        return kana_to_romaji(text)

    parts: list[str] = []
    pos = 0
    for m in _KANA_RE.finditer(text):
        if m.start() > pos:
            parts.append(" ".join(pypinyin.lazy_pinyin(text[pos:m.start()])))
        parts.append(kana_to_romaji(m.group()))
        pos = m.end()
    if pos < len(text):
        parts.append(" ".join(pypinyin.lazy_pinyin(text[pos:])))

    return " ".join(p for p in parts if p.strip())


def slugify(text: str, used: set[str]) -> str:
    """生成稳定、纯 ASCII 的目录名。"""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    ascii_only = ascii_only.encode("ascii", "ignore").decode("ascii")

    if len(re.sub(r"[^A-Za-z0-9]", "", ascii_only)) >= 2:
        base = ascii_only
    else:
        # 含中文 / 日文：按原顺序转罗马字
        base = romanize(text)

    base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower()
    if not base:
        base = "track"

    candidate, n = base, 2
    while candidate in used:
        candidate = f"{base}-{n}"
        n += 1
    return candidate


# --- 读标签 ---------------------------------------------------------------
def read_meta(path: Path) -> tuple[str, str]:
    """返回 (歌名, 歌手)，读不到就退回文件名。"""
    title = artist = ""
    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(path, easy=True)
        if audio is not None and audio.tags:
            title = (audio.tags.get("title") or [""])[0].strip()
            artist = (audio.tags.get("artist") or [""])[0].strip()
    except Exception:
        pass

    if not title:
        title = path.stem
        # 常见的 "歌名 - 歌手" 文件名约定
        if " - " in title:
            head, tail = title.split(" - ", 1)
            title, artist = head.strip(), artist or tail.strip()
    return title, artist or "Unknown"


def extract_cover(path: Path) -> bytes | None:
    """从音频内嵌标签里取出封面原图字节。"""
    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(path)
        if audio is None:
            return None

        # MP3 (ID3 APIC)
        tags = getattr(audio, "tags", None)
        if tags is not None and hasattr(tags, "getall"):
            for frame in tags.getall("APIC"):
                return frame.data

        # FLAC
        pictures = getattr(audio, "pictures", None)
        if pictures:
            return pictures[0].data

        # M4A (MP4 covr)
        if tags is not None and "covr" in getattr(tags, "keys", lambda: [])():
            return bytes(tags["covr"][0])
    except Exception:
        pass
    return None


def find_sidecar(path: Path, exts: set[str]) -> Path | None:
    """找同目录同名的封面图 / 歌词文件。"""
    for ext in exts:
        for candidate in (path.with_suffix(ext), path.with_suffix(ext.upper())):
            if candidate.exists():
                return candidate
    return None


def write_cover(raw: bytes | None, src_image: Path | None, dest: Path) -> bool:
    from PIL import Image

    try:
        if src_image is not None:
            img = Image.open(src_image)
        elif raw is not None:
            import io

            img = Image.open(io.BytesIO(raw))
        else:
            return False

        img = img.convert("RGB")
        side = min(img.size)
        left = (img.width - side) // 2
        top = (img.height - side) // 2
        img = img.crop((left, top, left + side, top + side))
        # 小图不放大（放大只会变糊），大图缩到 512
        if side > 512:
            img = img.resize((512, 512), Image.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, "WEBP", quality=88, method=6)
        return True
    except Exception as exc:
        print(f"    ! 封面处理失败：{exc}")
        return False


def write_lrc(src: Path, dest: Path) -> bool:
    """歌词统一转成 UTF-8，国内下载的 lrc 很多是 GBK。"""
    for enc in ("utf-8-sig", "utf-8", "gbk", "shift_jis"):
        try:
            text = src.read_text(encoding=enc)
            dest.write_text(text, encoding="utf-8")
            return True
        except (UnicodeDecodeError, LookupError):
            continue
    print(f"    ! 歌词编码识别失败：{src.name}")
    return False


# --- 主流程 ---------------------------------------------------------------
def check_deps() -> bool:
    missing = []
    try:
        import mutagen  # noqa: F401
    except ImportError:
        missing.append("mutagen")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        missing.append("Pillow")

    if missing:
        print("缺少依赖：" + "、".join(missing))
        print("安装：pip install " + " ".join(missing))
        return False

    try:
        import pypinyin  # noqa: F401
    except ImportError:
        print("提示：没装 pypinyin，中文歌名会退化成 track-1 这类编号。")
        print("      想要拼音目录名：pip install pypinyin\n")
    return True


def load_existing() -> list[dict]:
    if not MUSIC_JSON.exists():
        return []
    try:
        data = json.loads(MUSIC_JSON.read_text(encoding="utf-8"))
        return list(data.get("songs") or [])
    except (json.JSONDecodeError, OSError):
        return []


def main() -> int:
    parser = argparse.ArgumentParser(description="整理本地音乐到 public/music/")
    parser.add_argument("--inbox", default="music-inbox", help="音频来源目录，默认 music-inbox/")
    parser.add_argument("--list", action="store_true", help="只预览，不写文件")
    parser.add_argument("--reset", action="store_true", help="忽略已有歌单，全部重新生成")
    args = parser.parse_args()

    if not check_deps():
        return 1

    inbox = Path(args.inbox)
    if not inbox.is_absolute():
        inbox = ROOT / inbox

    if not inbox.exists():
        inbox.mkdir(parents=True)
        print(f"已创建 {inbox}，把音频丢进去再跑一次。")
        return 0

    files = sorted(p for p in inbox.iterdir() if p.suffix.lower() in AUDIO_EXT)
    if not files:
        print(f"{inbox} 里没有音频文件（支持 {', '.join(sorted(AUDIO_EXT))}）。")
        return 0

    existing = [] if args.reset else load_existing()
    # 歌名 → 已有 slug，保证改标签不换 URL
    slug_by_name = {s.get("name", ""): s.get("slug") for s in existing if s.get("slug")}
    used_slugs = {s["slug"] for s in existing if s.get("slug")}
    used_slugs |= {
        re.sub(r"[^a-z0-9]+", "-", s["name"].lower()).strip("-")
        for s in existing
        if not s.get("slug")
    }

    songs: list[dict] = []
    kept = {s.get("name") for s in existing}

    print(f"来源：{inbox}")
    print(f"找到 {len(files)} 个音频文件\n")

    for path in files:
        title, artist = read_meta(path)
        print(f"  {path.name}")
        print(f"    歌名：{title}    歌手：{artist}")

        slug = slug_by_name.get(title)
        if not slug:
            slug = slugify(title, used_slugs)
            used_slugs.add(slug)
        print(f"    slug：{slug}")

        entry = {
            "name": title,
            "artist": artist,
            "slug": slug,
            "format": path.suffix.lower().lstrip("."),
        }

        if not args.list:
            dest_dir = PUBLIC_MUSIC / slug
            dest_dir.mkdir(parents=True, exist_ok=True)

            audio_dest = dest_dir / f"{slug}{path.suffix.lower()}"
            if not audio_dest.exists() or audio_dest.stat().st_size != path.stat().st_size:
                shutil.copy2(path, audio_dest)
                print(f"    音频 → {audio_dest.relative_to(ROOT)}")

            embedded = extract_cover(path)
            sidecar_img = find_sidecar(path, IMAGE_EXT)
            using_fallback = embedded is None and sidecar_img is None
            if using_fallback and DEFAULT_COVER.exists():
                sidecar_img = DEFAULT_COVER

            if write_cover(embedded, sidecar_img, dest_dir / f"{slug}.webp"):
                entry["cover"] = True
                suffix = "（用站点头像兜底）" if using_fallback else ""
                print(f"    封面 → {slug}.webp{suffix}")

            sidecar_lrc = find_sidecar(path, {".lrc"})
            if sidecar_lrc and write_lrc(sidecar_lrc, dest_dir / f"{slug}.lrc"):
                entry["lrc"] = True
                print(f"    歌词 → {slug}.lrc")

        songs.append(entry)
        kept.discard(title)
        print()

    # 输入目录里没出现、但歌单里有的歌，保留在末尾
    for song in existing:
        if song.get("name") in kept:
            songs.append(song)

    print(f"共 {len(songs)} 首")
    if args.list:
        print("\n（--list 预览模式，没有写任何文件）")
        return 0

    MUSIC_JSON.write_text(
        json.dumps({"cdnUrl": "/music/", "songs": songs}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"歌单已写入 {MUSIC_JSON.relative_to(ROOT)}")
    print("\n下一步：pnpm dev 本地预览，或 pnpm generate 重新构建。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
