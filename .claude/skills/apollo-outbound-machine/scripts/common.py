"""Shared helpers. Stdlib only. Run scripts with: python3 -I <script>.py ..."""
import re, html

FOCUS = {"robotics_vision": "robotics", "llm_agents": "LLM", "bio_health": "biotech AI",
         "video_media": "generative video", "data_ml_infra": "ML infrastructure"}
AREA = {"robotics_vision": "robotics and computer vision", "llm_agents": "LLMs and agents",
        "bio_health": "AI for biotech", "video_media": "generative video and audio",
        "data_ml_infra": "ML and data infrastructure", "other_ai": "AI and ML"}
WL = {"robotics_vision": "perception model retraining", "llm_agents": "fine-tuning and eval runs",
      "bio_health": "protein and omics model runs", "video_media": "video and audio model training",
      "data_ml_infra": "training and eval runs", "other_ai": "GPU training and eval runs"}
BR = {
    "robotics_vision": "I'd guess perception and policy models get retrained and evaluated in bursts as new data arrives, which is where flexible GPU capacity helps.",
    "llm_agents": "I'd guess fine-tunes and eval sweeps come in bursts around each release, which is where flexible capacity helps.",
    "bio_health": "I'd guess model runs on new experimental batches come in bursts, which is where flexible GPU capacity helps.",
    "video_media": "I'd guess training and fine-tuning generation models comes in bursts around each release, which is where flexible capacity helps.",
    "data_ml_infra": "I'd guess training and eval jobs come in bursts around each experiment cycle, which is where flexible capacity helps.",
    "other_ai": "I'd guess training and eval runs come in bursts around each release, which is where flexible capacity helps.",
}
COMPLIANCE_SENTENCE = " We'd keep it to synthetic or de-identified data, since we're not a HIPAA environment."
ACR = {"gpu": "GPU", "gpus": "GPUs", "llm": "LLM", "llms": "LLMs", "ai": "AI", "ml": "ML", "3d": "3D", "rag": "RAG",
       "sql": "SQL", "nlp": "NLP", "asr": "ASR", "tts": "TTS", "african": "African", "api": "API", "ocr": "OCR",
       "iot": "IoT", "hpc": "HPC", "rna": "RNA", "dna": "DNA", "mri": "MRI", "cad": "CAD"}
SUF = re.compile(r",?\s*\b(Inc|LLC|L\.L\.C|Ltd|Limited|Corp|Corporation|GmbH|Co)\b\.?$", re.I)


def clean_company(n):
    """Display name for sentences: no legal suffix, no (YC W24) tags, no '| tagline'."""
    n = html.unescape(n or "")
    n = re.sub(r"\(.*?\)", "", n)
    n = re.split(r"\s+[|–—]\s+|\s+-\s+|:\s", n)[0]
    n = n.replace("™", "").replace("®", "")
    n = re.sub(r"\s+", " ", n).strip(" ,.")
    for _ in range(2):
        n = SUF.sub("", n).strip(" ,.")
    return n


def fix_workload_case(w):
    return re.sub(r"[A-Za-z0-9]+", lambda m: ACR.get(m.group(0).lower(), m.group(0)), w or "")


def words(s):
    return len((s or "").split())
