import json
import openai
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from infra.utils.azure_util import load_config


# Initialize the Flask application
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Load environment variables from the .env file in the root directory
load_dotenv()
config_data = load_config()

# Configure OpenAI client
openai_client = openai.OpenAI(api_key=config_data["OPENAI_KEY"])
embed_model = config_data["OPENAI_EMBED_MODEL"]

# Load the prompt template from the base_prompt.txt file
with open("./prompts/base_prompt.txt", "r") as f:
    PROMPT_TEMPLATE = f.read()

@app.route('/config', methods=['GET'])
def get_config():

    return jsonify(config_data)

# You can add a simple route to serve the static frontend files
@app.route('/')
def serve_index():
    return send_from_directory('dist', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('dist', path)


@app.route('/api/embed', methods=['POST'])
def embed_text():
    """
    Endpoint to generate an embedding for a given text using OpenAI.
    This protects the OpenAI API key by keeping it on the backend.
    """
    data = request.get_json()
    text = data.get("text")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        response = openai_client.embeddings.create(
            input=text,
            model=embed_model,
        )
        embedding = response.data[0].embedding
        return jsonify({"embedding": embedding})
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return jsonify({"error": "Failed to generate embedding"}), 500


def _generate_answer(query, retrieved_chunks, structured_records):
    """
    Generates an answer using the provided context and prompt template.
    """
    # Format the prompt with the retrieved data
    prompt = PROMPT_TEMPLATE.format(
        retrieved_chunks=retrieved_chunks,
        structured_records=json.dumps(structured_records),
        query=query
    )
    
    # Use the OpenAI API to get a completion
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",  # Or another appropriate chat model
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating answer from OpenAI: {e}")
        return "Sorry, I am unable to generate an answer at this time."
    

@app.route('/api/search', methods=['POST'])
def search_documents():
    """
    Performs a vector search on the Azure AI Search index.
    The search key is used securely on the backend.
    """
    try:
        data = request.get_json()
        search_payload = data.get('searchPayload')
        
        query = data.get('query')
        
        if not search_payload:
            return jsonify({"error": "No search payload provided."}), 400
        
        if not query:
            return jsonify({"error": "No query provided."}), 400

        search_endpoint = config_data["SEARCH_ENDPOINT"]
        index_name = config_data["INDEX_NAME"]
        search_key = config_data["SEARCH_API_KEY"]
        
        search_url = f"{search_endpoint}/indexes/{index_name}/docs/search?api-version=2025-05-01-Preview"
        print(f"Search URL: {search_url}")
        print(f"search key: {search_key}")
        response = requests.post(
            search_url,
            headers={
                'Content-Type': 'application/json',
                'api-key': search_key
            },
            json=search_payload
        )

        if not response.ok:
            return jsonify({"error": response.text}), response.status_code

        search_results = response.json()
        
        retrieved_chunks = ""
        structured_records = []
        
        for result in search_results.get("value", []):
            retrieved_chunks += f"Document ID: {result.get('id')}\n"
            retrieved_chunks += f"Content: {result.get('content')}\n"
            retrieved_chunks += f"Source: {result.get('source')}\n\n"
            
            # Assuming 'metadata' is a stringified JSON object
            metadata = json.loads(result.get('metadata', '{}'))
            structured_records.append(metadata)

        # Generate the final answer using the retrieved context and the query
        final_answer = _generate_answer(query, retrieved_chunks, structured_records)

        return jsonify({"answer": final_answer, "results": search_results.get("value")})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    # You might want to run this on a different port than your frontend dev server
    # to avoid conflicts, e.g., port 5000
    app.run(port=5000, debug=True)
