import React, { useState, useEffect } from 'react';

const App = () => {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isAppLoading, setIsAppLoading] = useState(true);

  useEffect(() => {
    setIsAppLoading(false);
  }, []);

  const embedText = async (text) => {
    try {
      const response = await fetch('/api/embed', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate embedding.");
      }

      const data = await response.json();
      return data.embedding;
    } catch (error) {
      console.error("Error generating embedding:", error);
      throw error;
    }
  };

  const handleSearch = async (event) => {
    event.preventDefault();
    if (!query /*|| !config*/) return;

    setLoading(true);
    setError('');
    setAnswer('');
    setResults([]);

    try {
      // Generate embedding for the search query via the backend
      const queryVector = await embedText(query);
      if (!queryVector) {
        setError("Failed to generate embedding for the query.");
        setLoading(false);
        return;
      }

      // Perform the vector search by calling the new backend search endpoint
      const searchPayload = {
        vectorQueries: [{
          "kind": "vector",
          "vector": queryVector,
          "k": 3,
          "fields": "contentVector",
          "exhaustive": true
        }],
        "select": "id, content, source, metadata",
        "queryType": "semantic",
        "semanticConfiguration": "my-semantic-config"
      };

      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          searchPayload: searchPayload,
          query: query
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Search request failed: ${errorData.error.message || errorData.error}`);
      }

      const data = await response.json();
      const lowerAnswer = data.answer.toLowerCase();
      // Handle "I don't know" and similar responses from the backend
      if (lowerAnswer.includes("i don't know.") || lowerAnswer.includes("i'm sorry")) {
        setAnswer("Sorry, I couldn't find an answer in the provided documents.");
        setResults([]);
      } else {
        setAnswer(data.answer);
        setResults(data.results);
      }

    } catch (err) {
      console.error('Search error:', err);
      setError(`An error occurred during the search: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (isAppLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-xl text-gray-700 animate-pulse">Loading configuration...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8 flex flex-col items-center">
      <div className="w-full max-w-4xl bg-white shadow-lg rounded-xl p-8">
        <h1 className="text-4xl font-extrabold text-center text-gray-800 mb-6">
          Products Search Explorer
        </h1>

        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-4 mb-8">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query..."
            className="flex-grow p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
          />
          <button
            type="submit"
            className="bg-blue-600 text-white font-semibold py-4 px-8 rounded-lg shadow-md hover:bg-blue-700 transition-colors duration-200 disabled:bg-gray-400"
            disabled={loading}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        {error && <div className="bg-red-100 text-red-700 p-4 rounded-lg mb-4">{error}</div>}

        {answer && (
          <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-400 rounded-lg">
            <h2 className="text-xl font-semibold mb-2 text-blue-800">Answer</h2>
            <p className="text-gray-700">{answer}</p>
          </div>
        )}

        {results.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-gray-700 mb-4">Search Results</h2>
            <ul className="space-y-4">
              {results.map((result, index) => (
                <li key={result.id} className="p-4 border border-gray-200 rounded-lg shadow-sm bg-gray-50">
                  <h3 className="font-bold text-lg text-gray-800 mb-1">Result {index + 1}</h3>
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold">Source:</span> {result.source}
                  </p>
                  <p className="text-gray-700 mt-2">{result.content}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
