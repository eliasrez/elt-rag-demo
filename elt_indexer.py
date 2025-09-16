import os
import uuid
import json
from openai import OpenAI
import pandas as pd
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SimpleField,
    ComplexField,
    SearchField,
    SearchFieldDataType,    
    SearchableField,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    VectorSearch, 
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    ExhaustiveKnnAlgorithmConfiguration
)

from azure.core.credentials import AzureKeyCredential
from PyPDF2 import PdfReader
from infra.utils.azure_util import load_config
from text_preprocessor import TextPreprocessor

def embed(openai_client, text, model_name):
    """
    Generates an embedding for the given text using OpenAI's embedding model.
    """
    response = openai_client.embeddings.create(
        input=text,
        model=model_name
    )
    return response.data[0].embedding

def load_pdfs(folder_path):
    """
    Loads text content from all PDF files in a given folder.
    """
    all_text = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            try:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    all_text.append(page.extract_text())
            except Exception as e:
                print(f"Error reading PDF file {filename}: {e}")
    return "\n".join(all_text)


def load_csv(csv_path, text_field="description"):
    df = pd.read_csv(csv_path)
    docs = []
    for _, row in df.iterrows():
        doc = {
            "id": str(uuid.uuid4()),
            "content": row[text_field],
            "metadata": {
                "doc_type": "csv",
                "source": os.path.basename(csv_path),
                **row.to_dict()
            }
        }
        docs.append(doc)
    return docs

def load_csvs_from_directory(directory_path, text_field="description"):
    """
    Loads documents from all CSV files in a given directory.

    Args:
        directory_path (str): The path to the directory containing CSV files.
        text_field (str): The name of the column in the CSV to use as the
                          main content for the document. Defaults to "description".

    Returns:
        list: A list of dictionaries, where each dictionary represents a document
              with 'id', 'content', and 'metadata'.
    """
    all_docs = []
    
    # Check if the directory exists
    if not os.path.isdir(directory_path):
        print(f"Directory not found: {directory_path}")
        return []

    # Iterate over all files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory_path, filename)
            print(f"Processing CSV file: {file_path}")
            
            try:
                df = pd.read_csv(file_path)
                
                # Check if the text_field exists in the DataFrame
                if text_field not in df.columns:
                    print(f"Warning: '{text_field}' column not found in {filename}. Skipping.")
                    continue
                
                # Iterate through rows and create documents
                for _, row in df.iterrows():
                    doc = {
                        "id": str(uuid.uuid4()),
                        "content": row[text_field],
                        "metadata": {
                            "doc_type": "csv",
                            "source": filename,
                            **row.to_dict()
                        }
                    }
                    all_docs.append(doc)

            except pd.errors.ParserError as e:
                print(f"Error parsing {filename}: {e}. Skipping this file.")
            except Exception as e:
                print(f"An unexpected error occurred while processing {filename}: {e}.")

    return all_docs

def chunk_text(text, chunk_size=1000):
    """
    Splits a large string into smaller chunks.
    """
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks

def create_index(config):

    """
    Deletes and re-creates the Azure AI Search index.
    
    Args:
        config (dict): The application configuration.
    """
    search_index_name = config["INDEX_NAME"]
    search_endpoint = config["SEARCH_ENDPOINT"]
    search_key = config["SEARCH_API_KEY"]
    
    index_client = SearchIndexClient(search_endpoint, AzureKeyCredential(search_key))

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchableField(name="source", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="metadata", type=SearchFieldDataType.String, searchable=False),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=config["EMBED_DIM"],
            vector_search_profile_name="my-vector-profile"
        )
    ]

    """vector_search=VectorSearch(
        algorithms=[
            VectorSearchAlgorithmConfiguration(
                name="default",
                kind="hnsw",
                hnsw_parameters=HnswParameters(metric="cosine")
            )
        ]
    )"""
    
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="my-hnsw-vector-config-1", kind="hnsw"),
            ExhaustiveKnnAlgorithmConfiguration(name="my-eknn-vector-config", kind="exhaustiveKnn")
        ],
        profiles=[
            VectorSearchProfile(name="my-vector-profile", algorithm_configuration_name="my-hnsw-vector-config-1")
        ]
    )
    """ vector_search = VectorSearch(
        algorithms=[HnswVectorSearchAlgorithmConfiguration(
            name="hnsw-config",
            parameters={"metric": "cosine", "m": 4, "efConstruction": 400}
        )],
        profiles=[VectorSearchProfile(name="default", algorithm_configuration_name="hnsw-config")]
    ) """

    index = SearchIndex(name=search_index_name, fields=fields, vector_search=vector_search)
    
    try:
        print(f"Deleting index '{search_index_name}'...")
        index_client.delete_index(search_index_name)
    except Exception as e:
        print(f"Index '{search_index_name}' not found or error deleting. Continuing... ({e})")
        
    print(f"Creating new index '{search_index_name}'...")
    index_client.create_index(index)
    print("Index created successfully.")

def ingest_docs(config, docs):
    """
    Uploads a batch of documents to the search index.
    
    Args:
        config (dict): The application configuration.
        docs (list): A list of dictionaries representing the documents to ingest.
    """
    search_client = SearchClient(
        endpoint=config["SEARCH_ENDPOINT"],
        index_name=config["INDEX_NAME"],
        credential=AzureKeyCredential(config["SEARCH_API_KEY"])
    )
    
    batch = []
    for d in docs:
        # Preprocess text and generate the embedding
        processed_text = TextPreprocessor.preprocess_with_nltk(d["content"])
        emb = embed(config["openai_client"], processed_text, config["OPENAI_EMBED_MODEL"])
        batch.append({
            "id": d["id"],
            "content": d["content"],
            "contentVector": emb,
            "source": d["metadata"].get("source"),
            "doc_type": d["metadata"].get("doc_type"),
            "metadata": json.dumps(d["metadata"])
        })
    print(f"Uploading {len(batch)} documents to the index...")
    search_client.upload_documents(batch)
    print("Documents uploaded successfully.")

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    try:
        # 1. Load all configuration and secrets
        app_config = load_config()
        
        # Configure OpenAI client
        #openai.api_type = "azure"
        #openai.api_base = app_config["OPENAI_ENDPOINT"]
        #openai.api_version = "2023-05-15"
        #openai.api_key = app_config["OPENAI_KEY"]
        app_config["openai_client"] = OpenAI(api_key=app_config["OPENAI_KEY"])

        # 2. Create the search index
        create_index(app_config)

        # 3. Ingest documents (example)
        # Note: The 'data/contoso_policy.pdf' path is hardcoded for this example.
        # You would typically make this more dynamic.
        pdf_text = load_pdfs("data/pdfs")
        pdf_chunks = chunk_text(pdf_text)
        
        pdf_docs = [
            {
                "id": str(uuid.uuid4()),
                "content": chunk,
                "metadata": {
                    "source": "contoso_policy.pdf",
                    "doc_type": "policy"
                }
            }
            for chunk in pdf_chunks
        ]
        
        # Example: CSV ingestion
        csv_docs = load_csvs_from_directory("data/csvs", text_field="description")
        all_docs = pdf_docs + csv_docs
        
         # Add OpenAI client to config for embedding function
        ingest_docs(app_config, all_docs)

    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
