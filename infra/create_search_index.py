import os
import requests
from pathlib import Path
from utils.azure_util import load_config


def create_search_index(config):
    """
    Deletes and re-creates the Azure AI Search index using the provided configuration.
    
    Args:
        config (dict): A dictionary containing all necessary configuration values.
    """
    if not config["SEARCH_API_KEY"]:
        print("API key not available. Exiting index creation.")
        return

    index_url = f"{config['SEARCH_ENDPOINT']}/indexes/{config['INDEX_NAME']}?api-version={config['SEARCH_API_VERSION']}"
    headers = {
        "Content-Type": "application/json",
        "api-key": config["SEARCH_API_KEY"]
    }

    index_definition = {
      "name": config["INDEX_NAME"],
      "fields": [
        {"name": "id", "type": "Edm.String", "key": True, "searchable": False},
        {"name": "content", "type": "Edm.String", "searchable": True, "analyzer": "en.lucene"},
        {"name": "source", "type": "Edm.String", "searchable": True, "filterable": True, "facetable": True},
        {"name": "doc_type", "type": "Edm.String", "searchable": True, "filterable": True, "facetable": True},
        {"name": "metadata", "type": "Edm.String", "searchable": False},
        # Vector field
        {
          "name": "contentVector",
          "type": "Collection(Edm.Single)",
          "searchAnalyzer": None,
          "dimensions": config["EMBED_DIM"],
          "vectorSearchProfile": "my-vector-profile"
        }
      ],
      "vectorSearch": {
          "profiles": [
              {
                  "name": "my-vector-profile",
                  "algorithm": "hnsw-config"
              }
          ],
          "algorithms": [
              {
                  "name": "hnsw-config",
                  "kind": "hnsw",
                  "hnswParameters": {
                      "metric": "cosine",
                      "m": 4,
                      "efConstruction": 400
                  }
              }
          ]
      }
    }

    # -------------------------------------------------------------------------
    # 2. Delete and create the index
    # -------------------------------------------------------------------------
    print(f"Deleting existing index '{config['INDEX_NAME']}' if it exists...")
    del_url = f"{config['SEARCH_ENDPOINT']}/indexes/{config['INDEX_NAME']}?api-version={config['SEARCH_API_VERSION']}"
    try:
        resp = requests.delete(del_url, headers=headers)
        if resp.status_code not in (200, 204, 404):
            print("Warning deleting index:", resp.status_code, resp.text)
    except requests.exceptions.RequestException as e:
        print(f"Error deleting index: {e}")
        return
        
    print(f"Creating new index '{config['INDEX_NAME']}'...")
    try:
        resp = requests.put(index_url, headers=headers, json=index_definition)
        if resp.status_code in (200, 201):
            print("Index created successfully.")
        else:
            print(f"Failed to create index: {resp.status_code} {resp.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error creating index: {e}")
        
if __name__ == "__main__":
    app_config = load_config()
    create_search_index(app_config)
