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
    },
    # Product (English)
    {
        "id": "8",
        "text": "Product Roadmap 2025: Our focus is on AI-powered features and enhanced user experience. Key products include the new analytics dashboard and automated workflow engine. Beta release scheduled for Q2.",
        "metadata": {"title": "Product Roadmap 2025", "category": "Product", "lang": "en"}
    },
    # Product (Japanese)
    {
        "id": "9",
        "text": "新機能リリース計画: 次期バージョンでは、リアルタイムコラボレーション機能と高度なレポート機能を追加予定です。ユーザーフィードバックに基づいて優先順位を決定しています。",
        "metadata": {"title": "New Feature Release Plan", "category": "Product", "lang": "ja"}
    },
    # Corporate (English)
    {
        "id": "10",
        "text": "Corporate Policy Update: New compliance requirements from Q1 2025. All employees must complete security training by March 31st. Updated code of conduct is now available in the employee portal.",
        "metadata": {"title": "Corporate Policy Update", "category": "Corporate", "lang": "en"}
    },
    # Corporate (Japanese)
    {
        "id": "11",
        "text": "人事制度の見直しについて: 2025年度より評価制度が変更されます。目標設定とフィードバックの頻度が増加し、より透明性の高い評価プロセスを目指します。詳細は人事部までお問い合わせください。",
        "metadata": {"title": "HR System Review", "category": "Corporate", "lang": "ja"}
    },
    # Engineering - Product Collaboration (English)
    {
        "id": "12",
        "text": "Engineering-Product Collaboration Guidelines: Cross-functional teams should follow the agile methodology. Weekly sync meetings are mandatory. Technical specifications must be reviewed by both Engineering and Product teams before implementation.",
        "metadata": {"title": "Engineering-Product Collaboration", "category": "Engineering", "lang": "en"}
    },
    # Sales - Product Collaboration (English)
    {
        "id": "13",
        "text": "Sales-Product Feedback Loop: Customer feedback from sales team is critical for product development. All feature requests must be documented in the shared portal. Monthly review meetings will prioritize roadmap items.",
        "metadata": {"title": "Sales-Product Feedback", "category": "Sales", "lang": "en"}
    },
    # Corporate - Security (English)
    {
        "id": "14",
        "text": "Security Incident Response Plan: In case of a security breach, immediately contact the security team. All incidents must be reported within 1 hour. Regular security audits will be conducted quarterly.",
        "metadata": {"title": "Security Incident Response", "category": "Corporate", "lang": "en"}
    }
]

# Document to folder mapping (Single Source of Truth)
DOC_TO_FOLDER = {
    "1": "engineering",
    "2": "sales",
    "3": "general",
    "4": "engineering",
    "5": "sales",
    "6": "general",
    "7": "executive",
    "8": "product",
    "9": "product",
    "10": "corporate",
    "11": "corporate",
    "12": "engineering",  # Engineering-Product collaboration doc accessible by both groups
    "13": "sales",  # Sales-Product collaboration doc accessible by both groups
    "14": "corporate",  # Security doc in corporate folder
}

# User data (Single Source of Truth)
USERS = [
    {"id": "user:seigen", "name": "Seigen", "role": "CEO", "groups": ["engineering", "sales", "product", "corporate"]},
    {"id": "user:alan", "name": "Alan", "role": "EM", "groups": ["engineering", "product"]},  # EM oversees Product team
    {"id": "user:tsukada", "name": "Tsukada", "role": "CRO", "groups": ["sales"]},
    {"id": "user:ando", "name": "Ando", "role": "Sales", "groups": ["sales"]},
    {"id": "user:ikeuchi", "name": "Ikeuchi", "role": "Corporate", "groups": ["corporate"]},
    {"id": "user:jinnai", "name": "Jinnai", "role": "Corporate", "groups": ["corporate"]},
    {"id": "user:kristine", "name": "Kristine", "role": "Product", "groups": ["product"]},
    {"id": "user:kurauchi", "name": "Kurauchi", "role": "SC/PM", "groups": ["scpm"]},  # SC/PM team
    {"id": "user:kuyama", "name": "Kuyama", "role": "SE", "groups": ["se"]},  # SE group
    {"id": "user:nakajima", "name": "Nakajima", "role": "Product", "groups": ["product"]},
    {"id": "user:shibata", "name": "Shibata", "role": "SE", "groups": ["se"]},  # SE group
    {"id": "user:tsukioka", "name": "Tsukioka", "role": "Hacker", "groups": []},  # ハッカー - 権限なし
]

# Profile image mapping (Single Source of Truth)
# Maps user ID (without "user:" prefix) to image filename
PROFILE_IMAGE_MAP = {
    "seigen": "seigen.png",
    "alan": "alan.png",
    "tsukada": "tsukada.png",
    "ando": "ando.png",
    "ikeuchi": "ikeuchi.png",
    "jinnai": "jinnai.png",
    "kristine": "kristine.png",
    "kurauchi": "kurauchi.png",
    "kuyama": "kuyama.png",
    "nakajima": "nakajima.png",
    "shibata": "shibata.png",
    "tsukioka": "tsukioka.png",
}

def get_documents():
    return [Document(text=d["text"], metadata=d["metadata"], doc_id=d["id"]) for d in docs_data]

def get_user_by_id(user_id: str):
    """Get user information by user ID."""
    return next((u for u in USERS if u["id"] == user_id), None)

def get_profile_image_path(user_id: str) -> str:
    """Get profile image path from user ID."""
    # Extract name from user ID (e.g., "user:seigen" -> "seigen")
    name = user_id.replace("user:", "").lower()
    image_name = PROFILE_IMAGE_MAP.get(name, f"{name}.png")
    return f"/static/img/{image_name}"
