import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

def get_secret_from_key_vault(vault_url, secret_name, secret_version=""):
    """
    Authenticates with Azure and retrieves a secret from Key Vault.

    Args:
        vault_url (str): The URL of the Azure Key Vault.
        secret_name (str): The name of the secret to retrieve.
        secret_version (str): The version of the secret to retrieve. Defaults to latest.

    Returns:
        str or None: The value of the secret if retrieval is successful, otherwise None.

    Raises:
        Any exception raised by the Azure SDK during authentication or secret retrieval will be caught,
        an error message will be printed, and None will be returned.
    """
    try:
        # Use DefaultAzureCredential to automatically handle authentication.
        # It will try multiple methods (e.g., Azure CLI, Managed Identity, etc.)
        credential = DefaultAzureCredential()
        
        # Create a SecretClient for your Key Vault
        client = SecretClient(vault_url=vault_url, credential=credential)
        
        # Get the secret
        secret = client.get_secret(secret_name, version=secret_version)
        
        return secret.value
    except Exception as ex:
        print(f"Error retrieving secret version '{secret_version}': {ex}")
        return None
    
def load_config():
    """
    Loads configuration from environment variables and returns a dictionary.
    
    This centralizes configuration management, making it easily accessible
    by other functions without re-reading environment variables.
    """
    load_dotenv()

    config = {
        "SEARCH_ENDPOINT": os.getenv("AZURE_SEARCH_ENDPOINT"),
        "KEY_VAULT_URL": os.getenv("AZURE_KEY_VAULT_URL"),
        "SEARCH_SECRET_NAME": os.getenv("AZURE_KEY_VAULT_SEARCH_SECRET_NAME"),
        "SEARCH_SECRET_VERSION": os.getenv("AZURE_KEY_VAULT_SEARCH_SECRET_VERSION", ""),
        "INDEX_NAME": os.getenv("AZURE_SEARCH_INDEX", "rag-demo-index"),
        "EMBED_DIM": int(os.getenv("EMBED_DIM", "1536")),
        "SEARCH_API_VERSION": os.getenv("SEARCH_API_VERSION", "2023-10-01-Preview"),
        "OPENAI_ENDPOINT": os.getenv("OPENAI_ENDPOINT"),
        "OPENAI_KEY_VAULT_NAME": os.getenv("AZURE_KEY_VAULT_OI_SECRET_NAME"),     
        "OPENAI_KEY_VAULT_SECRET_VERSION": os.getenv("AZURE_KEY_VAULT_OI_SECRET_VERSION"),
        "OPENAI_EMBED_MODEL": os.getenv("EMBED_MODEL", "text-embedding-3-small"), 
    }

    # Add API key from Key Vault to the config
    if not config["KEY_VAULT_URL"] or not config["SEARCH_SECRET_NAME"]:
        print("Please set the KEY_VAULT_URL and SECRET_NAME environment variables.")
        config["api_key"] = None
    else:
        api_key = get_secret_from_key_vault(
            config["KEY_VAULT_URL"], 
            config["SEARCH_SECRET_NAME"], 
            config["SEARCH_SECRET_VERSION"]
        )
        if api_key:
            print(f"Successfully retrieved API key. Length: {len(api_key)}")
            config["SEARCH_API_KEY"] = api_key
        else:
            config["SEARCH_API_KEY"] = None
            
    if not config["KEY_VAULT_URL"] or not config["OPENAI_KEY_VAULT_NAME"]:
        print("Please set the KEY_VAULT_URL and OPENAI_KEY_VAULT_NAME environment variables.")
        config["OPENAI_KEY"] = None
    else:
        config["OPENAI_KEY"] = get_secret_from_key_vault(
            config["KEY_VAULT_URL"], 
            config["OPENAI_KEY_VAULT_NAME"],
            config["OPENAI_KEY_VAULT_SECRET_VERSION"]
        )
            
    return config
