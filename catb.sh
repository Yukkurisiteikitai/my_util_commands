# ファイルの内容をMarkdownコードブロックとしてクリップボードにコピーする関数
function catb() {
  # --- 1. 引数（ファイル名）のチェック ---
  if [ -z "$1" ]; then
    echo "エラー: ファイル名を指定してください。"
    echo "使い方: catb <ファイル名>"
    return 1 # エラーとして終了
  fi

  # --- 2. ファイルの存在チェック ---
  if [ ! -f "$1" ]; then
    echo "エラー: ファイル '$1' が見つかりません。"
    return 1
  fi

  local filename="$1"

  # --- 3. Markdown形式の文字列を生成 ---
  # printf を使うと、より安全に文字列を組み立てられる
  # 最後の \n は、コピー後のペースト時に改行が入るようにするため
  local formatted_text
  formatted_text=$(printf "\`\`\`%s\n%s\n\`\`\`\n" "$filename" "$(cat "$filename")")

  # --- 4. OSを判別してクリップボードにコピー ---
  # command -v でコマンドの存在を確認
  if command -v pbcopy > /dev/null 2>&1; then
    # macOSの場合
    echo -n "$formatted_text" | pbcopy
    echo "✅ ファイル '$filename' の内容をクリップボードにコピーしました。(macOS)"
  elif command -v clip.exe > /dev/null 2>&1; then
    # Windows (WSL) の場合
    echo -n "$formatted_text" | clip.exe
    echo "✅ ファイル '$filename' の内容をクリップボードにコピーしました。(Windows/WSL)"
  elif command -v xclip > /dev/null 2>&1; then
    # Linux (X11) の場合
    echo -n "$formatted_text" | xclip -selection clipboard
    echo "✅ ファイル '$filename' の内容をクリップボードにコピーしました。(Linux/xclip)"
  else
    echo "エラー: クリップボードにコピーするコマンドが見つかりません。(pbcopy, clip.exe, xclip)"
    return 1
  fi
}