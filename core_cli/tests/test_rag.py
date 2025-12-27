import os
import sys

# Ensure workspace root is on sys.path when running tests directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from appshell.core.rag_service import SimpleVectorStore


def test_basic_retrieval():
    store = SimpleVectorStore(dim=128)
    store.add('doc1', 'Customer onboarding guide and setup instructions.', {'title': 'Onboarding'})
    store.add('doc2', 'Predictive maintenance for industrial sensors and anomaly detection.', {'title': 'Maintenance'})
    store.add('doc3', 'Marketing campaign analysis and A/B testing results.', {'title': 'Marketing'})

    results = store.search('predictive maintenance sensors', k=1)
    assert results, 'No results returned'
    top = results[0]
    assert top['doc_id'] == 'doc2', f"Expected doc2, got {top['doc_id']}"
    print('✅ RAG retrieval test passed — top result:', top['doc_id'])


if __name__ == '__main__':
    test_basic_retrieval()
