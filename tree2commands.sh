#!/bin/bash

# tree2commands.sh - ディレクトリツリーからコマンド列を生成

show_usage() {
  cat << EOF
Usage: tree2commands [OPTIONS] [TREE_FILE]

ディレクトリツリー形式からコマンド列を生成します。

OPTIONS:
  -c, --command CMD    使用するコマンド (デフォルト: catb)
  -o, --output FILE    出力ファイル名 (デフォルト: output.md または _t2c_output.md)
  -a, --append CMD     各コマンド後に実行するコマンド (デフォルト: pbpaste >> OUTPUT)
  -h, --help           このヘルプを表示

EXAMPLES:
  # 標準入力から読み込み (catb + pbpaste >> output.md)
  tree | tree2commands

  # ファイルから読み込み
  tree2commands tree.txt

  # 異なるコマンドを使用
  tree2commands -c cat -o result.md

  # カスタム追加コマンド
  tree2commands -c cat -a "xclip -selection clipboard | tee -a result.md"

NOTE:
  - output.mdが既に存在する場合、自動的に_t2c_output.mdを使用します
  - 実行後、生成されたファイルはpbcopyでクリップボードにコピーされ、削除されます

EOF
}

# デフォルト値
COMMAND="catb"
OUTPUT=""
APPEND_CMD=""
INPUT_FILE=""
OUTPUT_SPECIFIED=false

# オプション解析
while [[ $# -gt 0 ]]; do
  case $1 in
    -c|--command)
      COMMAND="$2"
      shift 2
      ;;
    -o|--output)
      OUTPUT="$2"
      OUTPUT_SPECIFIED=true
      shift 2
      ;;
    -a|--append)
      APPEND_CMD="$2"
      shift 2
      ;;
    -h|--help)
      show_usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      show_usage
      exit 1
      ;;
    *)
      INPUT_FILE="$1"
      shift
      ;;
  esac
done

# 出力ファイル名の決定 (output.mdが存在する場合は_t2c_output.mdを使用)
if [[ -z "$OUTPUT" ]]; then
  if [[ -f "output.md" ]]; then
    OUTPUT="_t2c_output.md"
    echo "Note: output.md already exists. Using _t2c_output.md instead." >&2
  else
    OUTPUT="output.md"
  fi
fi

# デフォルトの追加コマンド
if [[ -z "$APPEND_CMD" ]]; then
  APPEND_CMD="pbpaste >> $OUTPUT"
fi

# 入力の読み込み
if [[ -n "$INPUT_FILE" ]]; then
  if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: File not found: $INPUT_FILE" >&2
    exit 1
  fi
  TREE_INPUT=$(cat "$INPUT_FILE")
else
  TREE_INPUT=$(cat)
fi

# ツリー形式を解析してファイルパスを抽出
extract_files() {
  echo "$TREE_INPUT" | awk '
    BEGIN { 
      depth = 0
      path[0] = ""
    }
    
    # 空行やディレクトリツリーのヘッダーをスキップ
    /^$/ || /^\./ { next }
    
    # ファイル/ディレクトリ行を処理
    {
      # インデントレベルを計算 (├──, │, └── などの記号を考慮)
      line = $0
      gsub(/^[[:space:]]*/, "", line)  # 先頭の空白を削除
      
      # ツリー記号を削除してファイル名を取得
      gsub(/^[├└]──[[:space:]]*/, "", line)
      gsub(/^│[[:space:]]*/, "", line)
      
      # 空行またはディレクトリ数のサマリーをスキップ
      if (line == "" || line ~ /^[0-9]+ director/) next
      
      # インデントの深さを計算
      match($0, /^[[:space:]]*/)
      indent = RLENGTH
      curr_depth = int(indent / 4)
      
      # ディレクトリかファイルかを判定 (行末に / がない場合はファイル)
      is_dir = (line ~ /\/$/)
      gsub(/\/$/, "", line)  # 末尾の / を削除
      
      # パスを構築
      if (curr_depth == 0) {
        path[0] = line
      } else {
        path[curr_depth] = line
      }
      
      # ファイルの場合のみ出力
      if (!is_dir && line != "") {
        full_path = ""
        for (i = 1; i <= curr_depth; i++) {
          if (path[i] != "") {
            if (full_path != "") full_path = full_path "/"
            full_path = full_path path[i]
          }
        }
        print full_path
      }
    }
  '
}

# ファイルパスを抽出
FILES=$(extract_files)

# コマンド列を生成
if [[ -z "$FILES" ]]; then
  echo "Warning: No files found in tree structure" >&2
  exit 1
fi

echo "$FILES" | while IFS= read -r file; do
  if [[ -n "$file" ]]; then
    echo "$COMMAND $file"
    echo "$APPEND_CMD"
  fi
done

# 生成されたファイルをクリップボードにコピーして削除
if [[ -f "$OUTPUT" ]]; then
  pbcopy < "$OUTPUT"
  echo "✓ $OUTPUT copied to clipboard" >&2
  rm "$OUTPUT"
  echo "✓ $OUTPUT deleted" >&2
fi
