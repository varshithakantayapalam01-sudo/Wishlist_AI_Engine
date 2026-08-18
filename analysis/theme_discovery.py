"""
Theme Discovery Module.
Uses TF-IDF and K-Means clustering to discover emerging themes and
unmet needs outside the predefined taxonomy.
"""

import logging
import json
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import Counter

logger = logging.getLogger(__name__)

class ThemeDiscoverer:
    """Discovers emerging themes using unsupervised clustering."""

    def __init__(self, num_clusters: int = 10):
        self.num_clusters = num_clusters
        # Use English stop words, plus some shopping-specific noise words
        self.stop_words = "english"
        self.vectorizer = TfidfVectorizer(
            stop_words=self.stop_words,
            max_df=0.85,
            min_df=5,
            ngram_range=(1, 3)
        )

    def discover_themes(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run clustering on classified records to find themes."""
        if len(records) < self.num_clusters:
            logger.warning("Not enough records for theme discovery.")
            return []

        # Only cluster records with some substance
        valid_records = [
            r for r in records
            if len(str(r.get("original_text", ""))) > 50
        ]
        
        if not valid_records:
            return []

        texts = [r["original_text"] for r in valid_records]
        
        logger.info(f"Theme Discovery: Vectorizing {len(texts)} texts...")
        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            # Use get_feature_names for scikit-learn < 1.0 compatibility
            feature_names = self.vectorizer.get_feature_names() if hasattr(self.vectorizer, 'get_feature_names') else self.vectorizer.get_feature_names_out()
        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
            return []

        logger.info(f"Theme Discovery: Clustering into {self.num_clusters} themes...")
        kmeans = KMeans(n_clusters=self.num_clusters, random_state=42, n_init=10)
        kmeans.fit(tfidf_matrix)

        clusters = {}
        for i, label in enumerate(kmeans.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(valid_records[i])

        # Extract top terms per cluster
        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
        
        themes = []
        for i in range(self.num_clusters):
            cluster_records = clusters.get(i, [])
            if len(cluster_records) < 20:
                continue # Skip very small clusters

            top_features = [feature_names[ind] for ind in order_centroids[i, :8]]
            
            # Find representative snippets (closest to centroid intuitively by just picking some from the cluster)
            # In a full implementation, we'd calculate distance to centroid.
            # Here we just pick records with high confidence or length.
            sorted_by_len = sorted(cluster_records, key=lambda x: len(str(x.get("original_text", ""))), reverse=True)
            snippets = [
                r.get("evidence_snippet", str(r.get("original_text", ""))[:150]) 
                for r in sorted_by_len[:3]
            ]

            # Aggregate dominant barrier and need for this cluster
            barriers = Counter([r.get("primary_purchase_barrier", "unknown") for r in cluster_records])
            needs = Counter([r.get("underlying_user_need", "unknown") for r in cluster_records])
            
            top_barrier = barriers.most_common(1)[0][0] if barriers else "unknown"
            top_need = needs.most_common(1)[0][0] if needs else "unknown"
            
            avg_conf = sum(r.get("classification_confidence", 0) for r in cluster_records) / len(cluster_records)

            theme_name = " / ".join(top_features[:3]).title()

            themes.append({
                "theme_name": theme_name,
                "keywords": top_features,
                "conversation_count": len(cluster_records),
                "percentage_of_dataset": round((len(cluster_records) / len(records)) * 100, 2),
                "main_purchase_barrier": top_barrier,
                "likely_user_need": top_need,
                "average_confidence": round(avg_conf, 3),
                "representative_snippets": snippets
            })

        # Sort by size
        themes.sort(key=lambda x: x["conversation_count"], reverse=True)
        return themes

    def save_themes(self, themes: List[Dict[str, Any]], filepath: str):
        """Save discovered themes to JSON."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(themes, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(themes)} emerging themes to {filepath}")
