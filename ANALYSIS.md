# プロジェクト分析結果

## プロジェクト概要

このプロジェクトは、**OpenFGA**と**LlamaIndex**を組み合わせた認証対応 AI エージェントのデモンストレーションアプリケーションです。ローカル LLM（LM Studio）を使用して、権限管理を組み込んだ RAG（Retrieval-Augmented Generation）システムを実装しています。

## 技術スタック

### コア技術

- **LlamaIndex**: RAG フレームワーク（ドキュメント検索と LLM 統合）
- **OpenFGA**: 認証・認可システム（Zanzibar ベースの Relationship-Based Access Control）
- **LM Studio**: ローカル LLM 実行環境（`ibm/granite-4-h-tiny`モデル）
- **HuggingFace**: 埋め込みモデル（`BAAI/bge-small-en-v1.5`）

### 依存関係

```
llama-index
openfga-sdk
python-dotenv
openai
llama-index-llms-openai
llama-index-embeddings-huggingface
```

## アーキテクチャ

### 処理フロー

1. **ユーザーが質問を送信**
2. **LlamaIndex が関連ドキュメントを検索**（類似度上位 5 件）
3. **各ドキュメントに対して OpenFGA で権限チェック**
4. **許可されたドキュメントのみを LLM のコンテキストに追加**
5. **LLM が回答を生成**

### シーケンス図

```
User → Agent: Question
Agent → Agent: Retrieve relevant documents
Loop For each document:
    Agent → FGA: Check Permission (user, viewer, doc_id)
    alt Allowed:
        FGA → Agent: Allowed
        Agent → Agent: Add to Context
    else Denied:
        FGA → Agent: Denied
        Agent → Agent: Discard
    end
Agent → LLM: Generate Answer (Question + Filtered Context)
LLM → Agent: Response
Agent → User: Final Answer
```

## 主要コンポーネント

### 1. `agent.py` - メインエージェント

**役割**: AI エージェントのコア実装

**主要機能**:

- `FGAPostprocessor`: LlamaIndex の`BaseNodePostprocessor`を拡張し、権限チェックを実装
- 非同期で OpenFGA の`check()`を呼び出し
- 許可されたノードのみを返す

**実装のポイント**:

- `asyncio.run()`を使用して非同期処理を実行
- ドキュメント ID を`document:{doc_id}`形式に変換して OpenFGA に送信
- エラーハンドリングが最小限（例外をキャッチしてログ出力のみ）

### 2. `data.py` - ドキュメントデータ

**役割**: サンプルドキュメントの定義

**内容**:

- 7 つのサンプルドキュメント（英語・日本語混在）
- カテゴリ: Engineering, Sales, General, Executive
- 各ドキュメントに ID とメタデータを付与

**ドキュメント一覧**:

1. Engineering Roadmap 2025 (英語)
2. Sales Targets 2025 (英語)
3. Public Notice (英語)
4. Project Alpha Specs (日本語)
5. Q4 Sales Report JP (日本語)
6. Remote Work Policy (日本語)
7. Confidential Merger Strategy (英語、Executive 限定)

### 3. `fga_setup.py` - OpenFGA 初期設定

**役割**: OpenFGA の初期セットアップ

**処理内容**:

1. Store 作成
2. 認証モデルの書き込み（`auth_model.json`から読み込み）
3. タプル（権限関係）の設定

**設定される権限関係**:

- グループメンバーシップ
- フォルダへのアクセス権限
- ドキュメントとフォルダの親子関係

### 4. `auth_model.json` - 認証モデル定義

**役割**: OpenFGA の認証モデル（スキーマ）定義

**タイプ定義**:

- `user`: ユーザー
- `group`: グループ（`member`関係を持つ）
- `folder`: フォルダ（`viewer`と`parent`関係を持つ）
- `document`: ドキュメント（`viewer`と`parent`関係を持つ）

**権限継承**:

- `document`の`viewer`権限は、親`folder`の`viewer`権限を継承
- `folder`の`viewer`権限は、親`folder`の`viewer`権限を継承
- `tupleToUserset`を使用して階層的な権限継承を実現

## 権限モデル

### グループ構成

- **`group:engineering`**: Alan, Tsuki, Seigen
- **`group:sales`**: Tsukada, Seigen

### フォルダ構成

- **`folder:engineering`**: Engineering ドキュメント（Engineering グループが閲覧可能）
- **`folder:sales`**: Sales ドキュメント（Sales グループが閲覧可能）
- **`folder:general`**: 一般通知（両グループが閲覧可能）
- **`folder:executive`**: 機密情報（Seigen のみ閲覧可能）

### ユーザー

- **`user:seigen`** (CEO): 全グループメンバー + Executive フォルダへの直接アクセス
- **`user:alan`** (EM): Engineering グループメンバー
- **`user:tsukada`** (CRO): Sales グループメンバー
- **`user:tsuki`** (Backend): Engineering グループメンバー

### ドキュメントとフォルダのマッピング

- `document:1` (Engineering Roadmap) → `folder:engineering`
- `document:2` (Sales Targets) → `folder:sales`
- `document:3` (Public Notice) → `folder:general`
- `document:4` (Project Alpha) → `folder:engineering`
- `document:5` (Sales Report) → `folder:sales`
- `document:6` (Remote Work) → `folder:general`
- `document:7` (Merger Strategy) → `folder:executive`

## 実装の特徴

### 強み

1. **ローカル LLM 使用**: API キー不要で完全にローカルで動作
2. **細かい権限制御**: ドキュメント単位での権限チェック
3. **階層的権限管理**: グループとフォルダによる柔軟な権限管理
4. **多言語対応**: 英語・日本語のドキュメントに対応

### 注意点・制約事項

1. **イベントループの問題**: `agent.py`の`asyncio.run()`が既存のイベントループで失敗する可能性（Jupyter 等）
2. **インデックスの永続化**: 毎回インデックスを再構築している（本番環境では永続化が必要）
3. **エラーハンドリング**: 最小限のエラーハンドリング（例外をキャッチしてログ出力のみ）
4. **環境変数**: `.env.example`ファイルが存在しない（README に記載されているが実際のファイルがない）

## 使用シナリオ

### 許可される例

- **Seigen が Engineering について質問** → 許可（Engineering グループメンバー）
- **Alan が Holiday について質問** → 許可（General フォルダは全員アクセス可能）

### 拒否される例

- **Tsukada が Engineering について質問** → 拒否（Sales グループのみ）
- **Tsuki が Sales について質問** → 拒否（Engineering グループのみ）

## 改善提案

### 1. インデックスの永続化

現在は毎回インデックスを再構築していますが、本番環境では永続化が必要です。

```python
# インデックスの保存
index.storage_context.persist(persist_dir="./storage")

# インデックスの読み込み
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)
```

### 2. エラーハンドリングの強化

OpenFGA 接続エラーや LLM 接続エラーに対する適切な処理を追加すべきです。

```python
try:
    response = await client.check(...)
except ConnectionError:
    # OpenFGA接続エラーの処理
    logger.error("Failed to connect to OpenFGA")
    # フォールバック処理やエラーレスポンスの返却
```

### 3. ログの構造化

デバッグと監査のために、構造化ログを導入すべきです。

```python
import logging
import json

logger = logging.getLogger(__name__)
logger.info(json.dumps({
    "event": "permission_check",
    "user": user_id,
    "document": doc_id,
    "allowed": allowed
}))
```

### 4. 設定の外部化

`.env.example`ファイルを作成し、必要な環境変数を明確にすべきです。

```env
# .env.example
FGA_API_URL=http://localhost:8080
FGA_STORE_ID=
LLM_API_BASE=http://127.0.0.1:1234/v1
LLM_MODEL=ibm/granite-4-h-tiny
LLM_API_KEY=lm-studio
```

### 5. テストの追加

権限チェックのユニットテストや統合テストを追加すべきです。

```python
def test_fga_postprocessor_allows_authorized_document():
    # テストコード
    pass
```

### 6. ドキュメント ID のマッピング改善

`data.py`のドキュメント ID（"1", "2", ...）と`fga_setup.py`のドキュメント ID（"document:1", "document:2", ...）の対応関係を明確にする。

### 7. 非同期処理の改善

既存のイベントループがある場合の処理を改善する。

```python
try:
    authorized_nodes = asyncio.run(check_permissions())
except RuntimeError as e:
    if "asyncio.run() cannot be called" in str(e):
        # 既存のイベントループがある場合の処理
        loop = asyncio.get_event_loop()
        authorized_nodes = loop.run_until_complete(check_permissions())
    else:
        raise
```

## まとめ

このプロジェクトは、認証対応 RAG システムの実装例として非常に優れたデモンストレーションです。OpenFGA と LlamaIndex を組み合わせることで、ドキュメント単位での細かい権限制御を実現しています。本番環境で使用する場合は、上記の改善提案を実装することで、より堅牢で保守性の高いシステムになるでしょう。
