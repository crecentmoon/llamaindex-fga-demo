from llama_index.core import Document

# Mock Documents
# IDs are numeric strings.

docs_data = [
    # Engineering (English)
    {
        "id": "1",
        "text": "The Engineering Roadmap 2025: We will focus on migrating to a microservices architecture and implementing AI-driven testing. Key milestone: Q3 release of the new API.",
        "metadata": {"title": "Engineering Roadmap 2025", "category": "Engineering", "lang": "en"}
    },
    # Sales (English)
    {
        "id": "2",
        "text": "Sales Targets 2025: The goal is to reach $10M ARR. Focus on the enterprise sector in the APAC region. Commission structure has been updated.",
        "metadata": {"title": "Sales Targets 2025", "category": "Sales", "lang": "en"}
    },
    # General (English)
    {
        "id": "3",
        "text": "Public Notice: The office will be closed on December 25th for the holidays. Happy Holidays to everyone!",
        "metadata": {"title": "Holiday Notice", "category": "General", "lang": "en"}
    },
    # Engineering (Japanese)
    {
        "id": "4",
        "text": "プロジェクトAlphaの技術仕様書: このプロジェクトでは、次世代の認証基盤を構築します。OAuth2.0とOIDCに完全準拠し、生体認証もサポートする予定です。リリースは来年の第2四半期を予定しています。",
        "metadata": {"title": "Project Alpha Specs", "category": "Engineering", "lang": "ja"}
    },
    # Sales (Japanese)
    {
        "id": "5",
        "text": "2024年度第4四半期営業報告: 日本市場における売上は前年比120%増を達成しました。特に金融業界向けの導入が進んでいます。来期は製造業へのアプローチを強化します。",
        "metadata": {"title": "Q4 Sales Report JP", "category": "Sales", "lang": "ja"}
    },
    # General (Japanese)
    {
        "id": "6",
        "text": "社内規定の改定について: 2025年1月1日より、リモートワーク規定が一部変更されます。週2回の出社が推奨されますが、介護や育児などの事情がある場合はフルリモートも可能です。",
        "metadata": {"title": "Remote Work Policy", "category": "General", "lang": "ja"}
    },
    # Confidential (Executive only)
    {
        "id": "7",
        "text": "Confidential Merger Strategy: We are in early talks to acquire Competitor X. This information is strictly confidential and limited to C-level executives.",
        "metadata": {"title": "Merger Strategy", "category": "Executive", "lang": "en"}
    }
]

def get_documents():
    return [Document(text=d["text"], metadata=d["metadata"], doc_id=d["id"]) for d in docs_data]
