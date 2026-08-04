import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/api";
import Icon from "../components/Icon";

function SearchPage({
    setActiveDocumentId
}) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);
    const navigate = useNavigate();

    const runSearch = async () => {
        if (!query.trim()) {
            return;
        }

        setLoading(true);
        setSearched(true);

        try {
            const response = await api.get("/search", {
                params: { q: query.trim() }
            });
            setResults(response.data);
        } catch (error) {
            console.log(error);
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    const goChatWithDocument = (documentId) => {
        setActiveDocumentId(documentId);
        navigate("/");
    };

    return (
        <div className="search-page">
            <div className="search-page-inner">
                <Link
                    to="/"
                    className="back-to-chat"
                >
                    <Icon name="chevron-left" size={14} /> Back to Chat
                </Link>

                <h2 className="search-page-title">
                    <Icon name="search" size={22} /> Search Documents
                </h2>
                <p className="search-page-subtitle">
                    Search the actual text content of everything you've uploaded.
                </p>

                <div className="search-bar">
                    <input
                        type="text"
                        className="search-bar-input"
                        placeholder="Search for a word or phrase..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                runSearch();
                            }
                        }}
                    />
                    <button
                        className="search-bar-btn"
                        onClick={runSearch}
                        disabled={loading || !query.trim()}
                    >
                        {loading ? "Searching..." : "Search"}
                    </button>
                </div>

                <div className="search-results">
                    {
                        searched && !loading && results.length === 0 &&
                        <div className="empty-sidebar">
                            <div className="empty-icon"><Icon name="search" size={26} /></div>
                            <p>No matches found</p>
                        </div>
                    }
                    {
                        results.map(
                            (result, index) => (
                                <div
                                    key={`${result.document_id}-${result.chunk_index}-${index}`}
                                    className="search-result"
                                    onClick={() =>
                                        goChatWithDocument(result.document_id)
                                    }
                                >
                                    <div className="search-result-file">
                                        <Icon
                                            name={
                                                result.file_name.toLowerCase().endsWith(".docx")
                                                ? "file-text"
                                                : "file"
                                            }
                                            size={14}
                                        />
                                        {result.file_name}
                                    </div>
                                    <p className="search-result-snippet">
                                        {result.snippet}
                                    </p>
                                </div>
                            )
                        )
                    }
                </div>
            </div>
        </div>
    );
}

export default SearchPage;
