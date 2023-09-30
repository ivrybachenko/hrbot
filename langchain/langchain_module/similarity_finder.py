from langchain.vectorstores.elasticsearch import ElasticsearchStore
from docs_uploader.embedding import embeddings

elastic_vector_search = ElasticsearchStore(
    es_url="http://localhost:9200",
    index_name="text-basic",
    embedding=embeddings,
#     strategy=ElasticsearchStore.ExactRetrievalStrategy()
    distance_strategy="COSINE",
#     strategy=ElasticsearchStore.SparseVectorRetrievalStrategy(),
#     strategy=ElasticsearchStore.ApproxRetrievalStrategy(
#         hybrid=True,
#     )
)

if __name__ == '__main__':
    docs = elastic_vector_search.similarity_search(query="больничный", k=5)
    print(docs)
