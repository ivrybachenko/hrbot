import os
from tqdm import tqdm
from langchain.schema.document import Document
from langchain.vectorstores import ElasticsearchStore

from embedding import embeddings


def load_document_to_docs(doc_path: str):
    doc_path = doc_path.replace('\\', '/')
    with open(doc_path, 'r', encoding='utf-8') as file:
        return Document(page_content=file.read())


def load_all_documents_from_directory(root_directory: str):
    all_documents = []
    total_files = 0

    for subdir, _, files in os.walk(root_directory):
        total_files += len(files)

    with tqdm(total=total_files) as pbar:
        for subdir, _, files in os.walk(root_directory):
            for file in files:
                full_path = os.path.join(subdir, file)
                document = load_document_to_docs(full_path)
                all_documents.append(document)
                pbar.update(1)
    print(total_files)
    return all_documents


root_directory = 'processed_docs'
all_documents = load_all_documents_from_directory(root_directory)

for d in all_documents:
    print(d, '\n')

db = ElasticsearchStore.from_documents(
    all_documents, embeddings, es_url="http://127.0.0.1:9200", index_name="text-basic")
db.client.indices.refresh(index="text-basic")
