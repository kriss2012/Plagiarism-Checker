"""Semantic embedding and similarity module using Sentence-Transformers (all-MiniLM-L6-v2).
Provides graceful offline and heuristic fallbacks so the application never crashes
if model weights or internet connectivity are unavailable.
"""

from typing import List, Optional, Tuple
import numpy as np
from app.utils.logger import logger

_model = None
_model_load_attempted = False
_model_available = False


def is_semantic_model_available() -> bool:
    """Checks if the sentence-transformers model is loaded and operational."""
    global _model_available
    return _model_available


def get_model_status_text() -> str:
    """Returns human-readable model status for UI display."""
    if _model_available:
        return "Loaded ✓ (all-MiniLM-L6-v2)"
    elif _model_load_attempted:
        return "Heuristic/Offline Mode (Semantic model unavailable)"
    else:
        return "Ready to load on demand"


def load_semantic_model(model_name: str = "all-MiniLM-L6-v2") -> bool:
    """Attempts to initialize SentenceTransformer with local cache preference."""
    global _model, _model_load_attempted, _model_available
    if _model is not None:
        return True

    _model_load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading sentence-transformers model '{model_name}'...")
        # local_files_only=False allows downloading if online, but catches network error gracefully
        _model = SentenceTransformer(model_name)
        _model_available = True
        logger.info("Semantic model loaded successfully.")
        return True
    except Exception as e:
        logger.warning(f"Semantic sentence-transformers model unavailable: {e}. Falling back to TF-IDF heuristics.")
        _model = None
        _model_available = False
        return False


class SemanticSimilarityEngine:
    """Computes semantic embedding cosine similarity between text units."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Computes semantic similarity percentage (0.0 to 100.0) between two text segments."""
        if not text_a.strip() or not text_b.strip():
            return 0.0

        if _model is not None:
            try:
                embeddings = _model.encode([text_a, text_b], convert_to_tensor=False)
                vec_a = embeddings[0]
                vec_b = embeddings[1]
                norm_a = np.linalg.norm(vec_a)
                norm_b = np.linalg.norm(vec_b)
                if norm_a == 0 or norm_b == 0:
                    return 0.0
                cos_sim = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
                return max(0.0, min(100.0, cos_sim * 100.0))
            except Exception as e:
                logger.error(f"Semantic similarity calculation error: {e}")

        # Graceful TF-IDF fallback when neural model is offline/unavailable
        return self._tfidf_fallback(text_a, text_b)

    def compute_batch_similarity(self, query_texts: List[str], corpus_texts: List[str]) -> np.ndarray:
        """Computes pairwise cosine similarity matrix between queries and corpus items."""
        if not query_texts or not corpus_texts:
            return np.zeros((len(query_texts), len(corpus_texts)))

        if _model is not None:
            try:
                q_embeds = _model.encode(query_texts, show_progress_bar=False)
                c_embeds = _model.encode(corpus_texts, show_progress_bar=False)
                # Normalize
                q_norm = q_embeds / (np.linalg.norm(q_embeds, axis=1, keepdims=True) + 1e-9)
                c_norm = c_embeds / (np.linalg.norm(c_embeds, axis=1, keepdims=True) + 1e-9)
                return np.dot(q_norm, c_norm.T) * 100.0
            except Exception as e:
                logger.warning(f"Batch semantic computation failed: {e}. Using TF-IDF fallback.")

        # TF-IDF fallback
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        try:
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
            all_texts = query_texts + corpus_texts
            tfidf_mat = vectorizer.fit_transform(all_texts)
            q_mat = tfidf_mat[:len(query_texts)]
            c_mat = tfidf_mat[len(query_texts):]
            sim_mat = cosine_similarity(q_mat, c_mat) * 100.0
            return sim_mat
        except Exception:
            return np.zeros((len(query_texts), len(corpus_texts)))

    def _tfidf_fallback(self, text_a: str, text_b: str) -> float:
        """Lightweight scikit-learn cosine similarity fallback."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(ngram_range=(1, 2))
            mat = vectorizer.fit_transform([text_a, text_b])
            cos = cosine_similarity(mat[0:1], mat[1:2])[0][0]
            return float(cos * 100.0)
        except Exception:
            # Basic token Jaccard fallback
            tokens_a = set(text_a.lower().split())
            tokens_b = set(text_b.lower().split())
            if not tokens_a or not tokens_b:
                return 0.0
            jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
            return float(jaccard * 100.0)
