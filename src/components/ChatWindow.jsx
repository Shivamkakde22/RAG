import {
    useState,
    useEffect,
    useRef
}

from "react";
import axios from "axios";
import api from "../api/api";
import Message from "./Message";
import Icon from "./Icon";

const SUGGESTED_PROMPTS = [
    { icon: "file-text", text: "What is this document about?" },
    { icon: "bar-chart", text: "Summarize the key points" },
    { icon: "search", text: "List the main topics covered" },
    { icon: "message", text: "Explain this in simple terms" }
];

function ChatWindow({
    currentSessionId,
    setCurrentSessionId,
    onSessionCreated,
    activeDocumentId,
    setActiveDocumentId,
    documents
}) {
    const [query, setQuery] = useState("");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [copiedIndex, setCopiedIndex] = useState(null);
    const [evalScores, setEvalScores] = useState({});
    const [evalLoadingIndex, setEvalLoadingIndex] = useState(null);
    const bottomRef = useRef(null);
    const abortControllerRef = useRef(null);

    const activeDocumentName = documents?.find(
        (doc) => doc.id === activeDocumentId
    )?.file_name;

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        if (currentSessionId) {
            api.get(`/sessions/${currentSessionId}/messages`)
                .then((response) => {
                    const loaded = response.data.flatMap((row) => [
                        { role: "user", content: row.question },
                        { role: "assistant", content: row.answer }
                    ]);
                    setMessages(loaded);
                    setEvalScores({});
                })
                .catch((error) => console.log(error));
        } else {
            setMessages([]);
            setEvalScores({});
        }
    }, [currentSessionId]);

    const askQuestion = async (overrideText) => {
        const question = overrideText ?? query;
        if (!question || loading) return;

        setMessages(prev => [...prev, { role: "user", content: question }]);
        setQuery("");
        setLoading(true);

        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            const response = await api.post(
                "/chat",
                {
                    query: question,
                    session_id: currentSessionId,
                    document_id: activeDocumentId
                },
                { signal: controller.signal }
            );

            setMessages(prev => [
                ...prev,
                {
                    role: "assistant",
                    content: response.data.answer,
                    chunks: response.data.chunks || [],
                    query_type: response.data.query_type
                }
            ]);

            if (!currentSessionId && response.data.session_id) {
                setCurrentSessionId(response.data.session_id);
                onSessionCreated?.();
            }
        } catch (error) {
            if (axios.isCancel(error) || error.code === "ERR_CANCELED") return;
            setMessages(prev => [
                ...prev,
                {
                    role: "assistant",
                    content: error.response?.data?.error || "Something went wrong"
                }
            ]);
        } finally {
            abortControllerRef.current = null;
            setLoading(false);
        }
    };

    const regenerateLast = async () => {
        if (loading) return;

        let lastUserContent = null;
        for (let i = messages.length - 1; i >= 0; i--) {
            if (messages[i].role === "user") {
                lastUserContent = messages[i].content;
                break;
            }
        }
        if (!lastUserContent) return;

        setLoading(true);
        try {
            const response = await api.post("/chat", {
                query: lastUserContent,
                session_id: currentSessionId,
                document_id: activeDocumentId
            });

            setMessages(prev => {
                const updated = [...prev];
                const lastIndex = updated.length - 1;
                const newMsg = {
                    role: "assistant",
                    content: response.data.answer,
                    chunks: response.data.chunks || [],
                    query_type: response.data.query_type
                };
                if (updated[lastIndex]?.role === "assistant") {
                    updated[lastIndex] = newMsg;
                } else {
                    updated.push(newMsg);
                }
                return updated;
            });
        } catch (error) {
            console.log(error);
            alert("Could not regenerate response");
        } finally {
            setLoading(false);
        }
    };

    const handleEvaluate = async (index) => {
        const msg = messages[index];
        if (!msg?.chunks?.length) return;

        let precedingQuery = null;
        for (let i = index - 1; i >= 0; i--) {
            if (messages[i].role === "user") {
                precedingQuery = messages[i].content;
                break;
            }
        }
        if (!precedingQuery) return;

        setEvalLoadingIndex(index);
        try {
            const response = await api.post("/evaluate", {
                query: precedingQuery,
                answer: msg.content,
                chunks: msg.chunks
            });
            setEvalScores(prev => ({ ...prev, [index]: response.data }));
        } catch (err) {
            console.error("Evaluate error:", err);
        } finally {
            setEvalLoadingIndex(null);
        }
    };

    const handleStop = () => {
        if (abortControllerRef.current) abortControllerRef.current.abort();
    };

    const handleEditMessage = (content) => setQuery(content);

    const handleCopy = async (content, index) => {
        try {
            await navigator.clipboard.writeText(content);
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 1500);
        } catch (error) {
            console.log(error);
        }
    };

    let lastUserMessageIndex = -1;
    let lastAssistantMessageIndex = -1;
    messages.forEach((msg, index) => {
        if (msg.role === "user") lastUserMessageIndex = index;
        if (msg.role === "assistant") lastAssistantMessageIndex = index;
    });

    return (
        <div className="chat-window">
            <div className="chat-header">
                <div>
                    <h2>Chat with your Documents</h2>
                    <p>Ask questions across everything you've uploaded</p>
                </div>
                {activeDocumentId && (
                    <div className="active-filter-badge">
                        <span className="active-filter-name">
                            {activeDocumentName || "1 document"}
                        </span>
                        <button
                            className="active-filter-clear"
                            onClick={() => setActiveDocumentId(null)}
                            title="Clear filter"
                        >
                            <Icon name="x" size={14} />
                        </button>
                    </div>
                )}
            </div>

            <div className="messages">
                <div className="messages-inner">
                    {messages.length === 0 && (
                        <div className="empty-chat">
                            <h2><Icon name="file-text" size={26} />Ask Anything</h2>
                            <p>Upload a PDF and start chatting</p>
                            <div className="suggested-prompts">
                                {SUGGESTED_PROMPTS.map((prompt) => (
                                    <button
                                        key={prompt.text}
                                        className="suggested-prompt"
                                        onClick={() => askQuestion(prompt.text)}
                                    >
                                        <Icon name={prompt.icon} size={16} />
                                        {prompt.text}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((msg, index) => (
                        <Message
                            key={index}
                            role={msg.role}
                            content={msg.content}
                            queryType={msg.query_type}
                            copied={copiedIndex === index}
                            onCopy={() => handleCopy(msg.content, index)}
                            onRegenerate={
                                msg.role === "assistant" &&
                                index === lastAssistantMessageIndex &&
                                !loading
                                    ? regenerateLast
                                    : null
                            }
                            onEdit={
                                msg.role === "user" &&
                                index === lastUserMessageIndex
                                    ? () => handleEditMessage(msg.content)
                                    : null
                            }
                            onEvaluate={
                                msg.role === "assistant" && msg.chunks?.length
                                    ? () => handleEvaluate(index)
                                    : null
                            }
                            evalScore={evalScores[index] || null}
                            evalLoading={evalLoadingIndex === index}
                        />
                    ))}

                    {loading && (
                        <div className="msg-row msg-assistant">
                            <div className="msg-meta">
                                <span className="msg-sender">
                                    <Icon name="bot" size={13} />
                                    DocMind
                                </span>
                            </div>
                            <div className="loader">
                                <div className="dot"></div>
                                <div className="dot"></div>
                                <div className="dot"></div>
                            </div>
                        </div>
                    )}
                    <div ref={bottomRef}></div>
                </div>
            </div>

            <div className="chat-input">
                <div className="chat-input-wrapper">
                    <input
                        type="text"
                        placeholder="Ask anything about your documents..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") askQuestion();
                        }}
                    />
                    {loading ? (
                        <button className="stop-btn" onClick={handleStop} title="Stop">
                            <Icon name="square" size={14} />
                        </button>
                    ) : (
                        <button
                            className="send-btn"
                            onClick={() => askQuestion()}
                            disabled={!query.trim()}
                            title="Send"
                        >
                            <Icon name="send" size={16} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

export default ChatWindow;
