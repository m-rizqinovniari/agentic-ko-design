"""
Claude Tools untuk AI Agent Ko-Desain
"""

CODESIGN_TOOLS = [
    {
        "name": "capture_insight",
        "description": "Tangkap dan simpan insight dari interaksi dalam sesi ko-desain. Gunakan untuk merekam pain points, kebutuhan, emosi, atau perilaku yang teridentifikasi.",
        "input_schema": {
            "type": "object",
            "properties": {
                "insight_type": {
                    "type": "string",
                    "enum": ["pain_point", "need", "emotion", "behavior"],
                    "description": "Tipe insight: pain_point (hambatan), need (kebutuhan), emotion (emosi), behavior (perilaku)"
                },
                "content": {
                    "type": "string",
                    "description": "Deskripsi insight yang ditangkap"
                },
                "source": {
                    "type": "string",
                    "enum": ["vi_user", "designer", "observation"],
                    "description": "Sumber insight: vi_user (dari user tunanetra), designer (dari designer), observation (dari observasi AI)"
                },
                "empathy_category": {
                    "type": "string",
                    "enum": ["says", "thinks", "does", "feels", "hears", "touches"],
                    "description": "Kategori untuk empathy map"
                },
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Prioritas insight"
                }
            },
            "required": ["insight_type", "content", "source"]
        }
    },
    {
        "name": "add_to_empathy_map",
        "description": "Tambahkan item ke empathy map. Empathy map memiliki 6 kategori khusus untuk user tunanetra: says, thinks, does, feels, hears, touches.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["says", "thinks", "does", "feels", "hears", "touches"],
                    "description": "Kategori empathy map"
                },
                "content": {
                    "type": "string",
                    "description": "Konten yang akan ditambahkan"
                },
                "source": {
                    "type": "string",
                    "enum": ["vi_user", "designer", "ai_observation"],
                    "description": "Sumber informasi"
                },
                "context": {
                    "type": "string",
                    "description": "Konteks atau situasi terkait"
                }
            },
            "required": ["category", "content", "source"]
        }
    },
    {
        "name": "add_to_journey_map",
        "description": "Tambahkan touchpoint atau informasi ke user journey map.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage": {
                    "type": "string",
                    "description": "Nama stage dalam journey (misal: 'Membuka Aplikasi', 'Input Nominal', 'Konfirmasi Pembayaran')"
                },
                "stage_order": {
                    "type": "integer",
                    "description": "Urutan stage (1, 2, 3, dst)"
                },
                "touchpoint": {
                    "type": "string",
                    "description": "Touchpoint atau interaksi dalam stage ini"
                },
                "action": {
                    "type": "string",
                    "description": "Aksi yang dilakukan user"
                },
                "thought": {
                    "type": "string",
                    "description": "Apa yang dipikirkan user"
                },
                "emotion": {
                    "type": "string",
                    "description": "Emosi yang dirasakan (positif/netral/negatif)"
                },
                "pain_point": {
                    "type": "string",
                    "description": "Hambatan atau kesulitan yang dialami"
                },
                "opportunity": {
                    "type": "string",
                    "description": "Peluang improvement"
                },
                "accessibility_note": {
                    "type": "string",
                    "description": "Catatan khusus terkait aksesibilitas"
                }
            },
            "required": ["stage", "stage_order"]
        }
    },
    {
        "name": "suggest_design_element",
        "description": "Sarankan elemen desain berdasarkan insight yang telah dikumpulkan. Fokus pada aksesibilitas untuk tunanetra.",
        "input_schema": {
            "type": "object",
            "properties": {
                "element_type": {
                    "type": "string",
                    "enum": ["button", "navigation", "feedback", "confirmation", "input", "notification", "gesture"],
                    "description": "Tipe elemen desain"
                },
                "name": {
                    "type": "string",
                    "description": "Nama elemen"
                },
                "description": {
                    "type": "string",
                    "description": "Deskripsi fungsionalitas elemen"
                },
                "accessibility_features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fitur aksesibilitas yang direkomendasikan"
                },
                "audio_feedback": {
                    "type": "string",
                    "description": "Deskripsi audio feedback untuk elemen ini"
                },
                "haptic_feedback": {
                    "type": "string",
                    "description": "Deskripsi haptic feedback untuk elemen ini"
                },
                "rationale": {
                    "type": "string",
                    "description": "Alasan mengapa elemen ini direkomendasikan"
                },
                "addresses_pain_point": {
                    "type": "string",
                    "description": "Pain point mana yang dijawab oleh elemen ini"
                }
            },
            "required": ["element_type", "name", "description", "rationale"]
        }
    },
    {
        "name": "mediate_disagreement",
        "description": "Mediasi perbedaan perspektif antara designer dan user tunanetra. Gunakan untuk membantu menemukan common ground.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topik yang diperdebatkan"
                },
                "perspective_vi_user": {
                    "type": "string",
                    "description": "Perspektif user tunanetra"
                },
                "perspective_designer": {
                    "type": "string",
                    "description": "Perspektif designer"
                },
                "common_ground": {
                    "type": "string",
                    "description": "Kesamaan yang ditemukan"
                },
                "suggested_compromise": {
                    "type": "string",
                    "description": "Kompromi yang disarankan"
                },
                "priority_recommendation": {
                    "type": "string",
                    "description": "Rekomendasi prioritas (accessibility-first atau balance)"
                }
            },
            "required": ["topic", "perspective_vi_user", "perspective_designer", "suggested_compromise"]
        }
    },
    {
        "name": "summarize_session",
        "description": "Buat rangkuman dari sesi atau fase ko-desain.",
        "input_schema": {
            "type": "object",
            "properties": {
                "phase": {
                    "type": "string",
                    "description": "Fase yang dirangkum"
                },
                "key_insights": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Insight kunci yang diperoleh"
                },
                "decisions_made": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keputusan yang telah dibuat"
                },
                "open_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Pertanyaan yang masih terbuka"
                },
                "next_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Langkah selanjutnya yang perlu dilakukan"
                }
            },
            "required": ["phase", "key_insights"]
        }
    },
    {
        "name": "request_clarification",
        "description": "Minta klarifikasi dari participant. Gunakan ketika ada informasi yang kurang jelas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "enum": ["vi_user", "designer", "both"],
                    "description": "Siapa yang diminta klarifikasi"
                },
                "question": {
                    "type": "string",
                    "description": "Pertanyaan klarifikasi"
                },
                "context": {
                    "type": "string",
                    "description": "Konteks mengapa perlu klarifikasi"
                }
            },
            "required": ["target", "question"]
        }
    },
    {
        "name": "validate_accessibility",
        "description": "Validasi apakah suatu desain atau fitur memenuhi standar aksesibilitas untuk tunanetra.",
        "input_schema": {
            "type": "object",
            "properties": {
                "feature_name": {
                    "type": "string",
                    "description": "Nama fitur yang divalidasi"
                },
                "feature_description": {
                    "type": "string",
                    "description": "Deskripsi fitur"
                },
                "has_audio_alternative": {
                    "type": "boolean",
                    "description": "Apakah ada alternatif audio?"
                },
                "has_haptic_feedback": {
                    "type": "boolean",
                    "description": "Apakah ada haptic feedback?"
                },
                "screen_reader_compatible": {
                    "type": "boolean",
                    "description": "Apakah kompatibel dengan screen reader?"
                },
                "voice_control_supported": {
                    "type": "boolean",
                    "description": "Apakah mendukung voice control?"
                },
                "issues_found": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Masalah aksesibilitas yang ditemukan"
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Rekomendasi perbaikan"
                }
            },
            "required": ["feature_name", "feature_description"]
        }
    }
]


def get_tools_for_phase(phase: str) -> list:
    """
    Get tools yang relevan untuk fase tertentu

    Args:
        phase: Nama fase ko-desain

    Returns:
        List of tools yang relevan
    """
    # Semua tools tersedia di semua fase, tapi bisa di-filter jika perlu
    phase_tools = {
        "setup": ["summarize_session"],
        "shared_framing": [
            "capture_insight",
            "add_to_empathy_map",
            "request_clarification"
        ],
        "perspective_exchange": [
            "capture_insight",
            "add_to_empathy_map",
            "add_to_journey_map",
            "request_clarification"
        ],
        "meaning_negotiation": [
            "suggest_design_element",
            "mediate_disagreement",
            "validate_accessibility",
            "summarize_session"
        ],
        "reflection_iteration": [
            "suggest_design_element",
            "validate_accessibility",
            "summarize_session"
        ],
        "complete": ["summarize_session"]
    }

    relevant_tool_names = phase_tools.get(phase, [])

    # Return semua tools untuk fleksibilitas, tapi prioritaskan yang relevan
    # Dalam implementasi real, bisa filter hanya tools yang relevan
    return CODESIGN_TOOLS
