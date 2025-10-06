
#!/bin/bash

# 引数（機能名）が指定されていない場合はエラーを表示して終了
if [ -z "$1" ]; then
  echo "エラー: 機能名を入力してください。"
  echo "使い方: git nb <機能名>"
  exit 1
fi

# ブランチタイプを選択肢として定義
PS3="番号を入力してください: "
options=("future" "fix" "search" "test")

echo "ブランチタイプを選択してください:"
select branch_type in "${options[@]}"; do
  # 有効な選択肢が選ばれたらループを抜ける
  if [[ " ${options[*]} " =~ " ${branch_type} " ]]; then
    break
  else
    echo "無効な選択です。もう一度選択してください。"
  fi
done

# Gitのconfigからユーザー名を取得
user_name=$(git config user.name)
if [ -z "$user_name" ]; then
  echo "エラー: Gitのユーザー名が設定されていません。git config --global user.name 'Your Name' で設定してください。"
  exit 1
fi

# 機能名を取得
feature_name=$1

# ブランチ名を組み立てる
branch_name="${branch_type}/${user_name}/${feature_name}"

# 組み立てたブランチ名で `git checkout -b` を実行
echo "ブランチ '${branch_name}' を作成します..."
git checkout -b "$branch_name"
