#!/usr/bin/env python3
"""
YouTube URL から video ID を抽出するスクリプト
重複を除去し、クリーンな URL として出力します。

使い方:
  # クリップボードから入力
  python yt_extract.py --clipboard

  # ファイルから入力
  python yt_extract.py --file input.txt

  # ファイルに出力
  python yt_extract.py --clipboard --output result.txt
"""

import re
import sys
import argparse
from urllib.parse import urlparse, parse_qs


def extract_video_id(url: str) -> str | None:
    """
    YouTube URL から video ID のみを抽出する。
    対応フォーマット:
      - https://www.youtube.com/watch?v=XXXX
      - https://youtu.be/XXXX
      - https://youtube.com/watch?v=XXXX&t=123  ← t= などは除外
      - https://m.youtube.com/watch?v=XXXX
    """
    url = url.strip()
    if not url:
        return None

    try:
        parsed = urlparse(url)
    except Exception:
        return None

    host = parsed.netloc.lower()

    # youtu.be/XXXX 形式
    if host in ("youtu.be", "www.youtu.be"):
        vid = parsed.path.lstrip("/").split("/")[0]
        return vid if re.fullmatch(r"[A-Za-z0-9_\-]{11}", vid) else None

    # youtube.com/watch?v=XXXX 形式
    if host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        vids = qs.get("v")
        if vids:
            vid = vids[0]
            return vid if re.fullmatch(r"[A-Za-z0-9_\-]{11}", vid) else None

    return None


def extract_all_video_ids(text: str) -> list[str]:
    """
    テキスト中の全 YouTube URL から video ID を抽出し、
    重複を除去した順序付きリストを返す。
    """
    # URL っぽい文字列を広めにマッチ
    url_pattern = re.compile(
        r"https?://[^\s\]\[<>\"'）)）、。\n]+"
    )

    seen: set[str] = set()
    ordered: list[str] = []

    for match in url_pattern.finditer(text):
        raw_url = match.group(0).rstrip(".,;:!?\"'）")
        vid = extract_video_id(raw_url)
        if vid and vid not in seen:
            seen.add(vid)
            ordered.append(vid)

    return ordered


def format_output(video_ids: list[str]) -> str:
    """video ID リストをクリーンな URL 形式に整形する。"""
    base = "https://www.youtube.com/watch?v="
    return "\n".join(base + vid for vid in video_ids)


def read_clipboard() -> str:
    """クリップボードからテキストを読み込む。"""
    try:
        import subprocess
        # macOS
        result = subprocess.run(["pbpaste"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass

    try:
        import subprocess
        # Linux (xclip)
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass

    try:
        import subprocess
        # Linux (xsel)
        result = subprocess.run(
            ["xsel", "--clipboard", "--output"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass

    try:
        # Windows / cross-platform fallback
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text
    except Exception:
        pass

    print("エラー: クリップボードの読み取りに失敗しました。", file=sys.stderr)
    print("pbpaste / xclip / xsel / tkinter のいずれかが必要です。", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="YouTube URL から video ID を抽出し、重複を除去してリスト出力します。"
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--file", "-f",
        metavar="PATH",
        help="入力ファイルのパス"
    )
    source.add_argument(
        "--clipboard", "-c",
        action="store_true",
        help="クリップボードから入力"
    )

    parser.add_argument(
        "--output", "-o",
        metavar="PATH",
        help="出力ファイルのパス（省略時は標準出力）"
    )

    args = parser.parse_args()

    # --- 入力 ---
    if args.clipboard:
        text = read_clipboard()
        source_label = "クリップボード"
    else:
        try:
            with open(args.file, encoding="utf-8") as f:
                text = f.read()
            source_label = args.file
        except FileNotFoundError:
            print(f"エラー: ファイルが見つかりません: {args.file}", file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"エラー: ファイルを開けません: {e}", file=sys.stderr)
            sys.exit(1)

    # --- 処理 ---
    video_ids = extract_all_video_ids(text)

    if not video_ids:
        print(f"[{source_label}] YouTube の video ID が見つかりませんでした。", file=sys.stderr)
        sys.exit(0)

    result = format_output(video_ids)

    # --- 出力 ---
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result + "\n")
            print(
                f"[完了] {len(video_ids)} 件の URL を {args.output} に書き出しました。",
                file=sys.stderr
            )
        except OSError as e:
            print(f"エラー: ファイルに書き込めません: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(result)


if __name__ == "__main__":
    main()
