# Streamlit 売上データ管理サンプル

CSV の売上データを絞り込み、顧客分類を編集し、売上集計をグラフで確認するシンプルな Streamlit アプリです。

## 機能

- 対象年（チェックボックス）と担当者（入力による候補絞り込みが可能な複数選択）でデータをフィルタ
- 表では「顧客分類」のみ編集可能
- 年月別売上金額を棒グラフで表示
- 顧客分類別売上金額を円グラフで表示
- 100 件のサンプルデータを同梱

> 編集内容はブラウザのセッション中のみ保持され、CSV ファイル自体には保存されません。

## 動かし方

Python 3.10 以上を推奨します。

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

コマンド実行後、通常はブラウザで `http://localhost:8501` が開きます。

## ファイル構成

```text
.
├── app.py              # Streamlit アプリ
├── sample_sales.csv    # サンプル売上データ（100件）
├── requirements.txt    # Python 依存パッケージ
└── README.md
```

CSV の列は `対象日付`, `担当者`, `顧客名`, `顧客分類`, `売上金額` です。`対象日付` は `YYYY-MM-DD` 形式、`売上金額` は整数で記録しています。
