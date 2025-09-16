# ELT + RAG Demo

This project demonstrates an end-to-end pipeline for **ELT (Extract-Load-Transform)** and **RAG (Retrieval-Augmented Generation)** using Azure Cognitive Search, OpenAI, and structured/unstructured sample data.  

The project also demonstrate use of Terraform (i.e Infrastructure as code) and use of Azure Key Vault for storing Azure search 
and OpenAI API keys.

The goal is to showcase how to:
- Ingest both PDFs and CSVs into a data pipeline
- Transform and embed data
- Index into Azure Cognitive Search (vector search enabled)
- Build a simple retrieval + LLM layer for Q&A and insights
- Deploy infrastructure with Terraform


---

## Simple demo UX
![alt text][screenshot]

[screenshot]: https://github.com/eliasrez/elt-rag-demo/blob/main/frontend/my-search-app/public/screenshot1.png "UX Screenshot"

## 📁 Project Structure

```
elt-rag-demo/
├── infra/terraform/        # Terraform configs for Azure (Search, Storage, OpenAI)
├── data/                   # Sample docs (PDFs, CSVs)
│   ├── contoso_policy.pdf
│   ├── contoso_it_security.pdf
│   ├── contoso_benefits.pdf
│   ├── products.csv
│   ├── employees.csv
│   └── customers.csv
├── elt_indexer.py          # Indexer: extracts, chunks, embeds, uploads
├── text_preprocessor.py    # Cleans and splits text
├── search_server.py        # Simple backend API for querying
├── prompts/                # Prompt templates for retrieval + generation
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Azure subscription  
- Terraform installed  
- Python 3.11+  
- Node.js (if running the frontend)  

### 2. Provision Azure Resources

```bash
cd infra/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

This creates:
- Azure Resource Group  
- Storage Account + Blob container  
- Cognitive Search service (vector enabled)  
- (Optional) Azure OpenAI resource  

### 3. Prepare Data
Put PDFs and CSVs into the `data/` folder. The repo already includes:
- Policies (PDFs)
- Products, Employees, Customers (CSVs)

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

```bash
export AZURE_SEARCH_ENDPOINT=<your-search-service-endpoint>
export AZURE_SEARCH_ADMIN_KEY=<admin-key>
export OPENAI_API_KEY=<your-openai-or-azure-openai-key>
export OPENAI_EMBEDDING_MODEL=text-embedding-3-small
export OPENAI_CHAT_MODEL=gpt-4o-mini
```

### 6. Run the Indexer

```bash
python elt_indexer.py
```

This script:
- Extracts text from PDFs and CSVs  
- Generates embeddings via OpenAI/Azure OpenAI  
- Uploads docs into Cognitive Search  

### 7. Run the Backend Server - All calls to openai and Azure search are handled in the backend for security

```bash
python search_server.py
```

### 8. Query
Send queries via API or frontend to test RAG responses:
- *“What are the company’s work hours?”*  
- *“Tell me about Contoso Phone XL.”*  
- *“Who works in Marketing in Boston?”*  

---

## ⚡ Features
- Hybrid ingestion: structured + unstructured  
- Vector search with HNSW indexing  
- Prompt templates for combining structured/unstructured context  
- Modular: swap in local vector DB (Qdrant, Weaviate) if desired  
- Infrastructure as Code with Terraform  

---

## 📦 Dependencies
- `azure-search-documents>=11.4.0b11` (preview for HNSW support)  
- `openai`  
- `fastapi` or `flask` (for API)  
- `pypdf` or `pdfplumber` (PDF parsing)  

Install all at once:
```bash
pip install -r requirements.txt
```

---

## 🔮 Roadmap
- Add streaming frontend UI  
- Role-based access control  
- Support for feedback loop / relevance tuning  
- Multi-lingual indexing  

---

## 📄 License
MIT License (or your chosen license).  

---

## ✨ Author
Built by **Elias Rez**  
For questions, open an issue or PR.
