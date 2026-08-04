import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api";
import Icon from "./Icon";

function formatDuration(totalSeconds) {
    if (totalSeconds == null) return null;
    const s = Math.max(0, Math.round(totalSeconds));
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return m > 0 ? `${m}m ${rem}s` : `${rem}s`;
}

function SettingsModal({
    documents,
    sessions,
    onClearHistory,
    onClose
}) {
    const [llmStatus, setLlmStatus] = useState(null);
    const [statusLoading, setStatusLoading] = useState(false);
    const [now, setNow] = useState(Date.now());
    const navigate = useNavigate();

    const fetchStatus = useCallback(async () => {
        setStatusLoading(true);
        try {
            const response = await api.get("/system/llm-status");
            setLlmStatus(response.data);
            setNow(Date.now());
        } catch (error) {
            console.log(error);
        } finally {
            setStatusLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchStatus();
    }, [fetchStatus]);

    useEffect(() => {
        const interval = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(interval);
    }, []);

    const remainingSeconds = (referenceIso, totalSeconds) => {
        if (!referenceIso || totalSeconds == null) return null;
        const elapsed = (now - new Date(referenceIso).getTime()) / 1000;
        return Math.max(0, totalSeconds - elapsed);
    };

    const handleClearHistory = async () => {
        const ok = window.confirm(
            "Delete all chat history? This can't be undone."
        );
        if (!ok) {
            return;
        }

        try {
            await api.delete("/sessions");
            onClearHistory();
        } catch (error) {
            console.log(error);
            alert("Could not clear chat history");
        }
    };

    return (
        <div
            className="modal-backdrop"
            onClick={onClose}
        >
            <div
                className="modal-card"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="modal-header">
                    <h3>Settings</h3>
                    <button
                        className="modal-close"
                        onClick={onClose}
                    >
                        <Icon name="x" size={14} />
                    </button>
                </div>

                <div className="settings-stats">
                    <div className="settings-stat">
                        <span className="settings-stat-value">
                            {documents.length}
                        </span>
                        <span className="settings-stat-label">
                            Documents
                        </span>
                    </div>
                    <div className="settings-stat">
                        <span className="settings-stat-value">
                            {sessions.length}
                        </span>
                        <span className="settings-stat-label">
                            Conversations
                        </span>
                    </div>
                </div>

                <div className="settings-usage">
                    <div className="settings-usage-header">
                        <span className="settings-section-label">
                            API Usage (Groq)
                        </span>
                        <button
                            className="settings-refresh-btn"
                            onClick={fetchStatus}
                            disabled={statusLoading}
                            title="Refresh"
                        >
                            <Icon name="refresh" size={13} />
                        </button>
                    </div>

                    {llmStatus?.per_minute?.tokens ? (
                        <div className="usage-row">
                            <span className="usage-label">Tokens / min</span>
                            <span className="usage-value">
                                {llmStatus.per_minute.tokens.remaining} / {llmStatus.per_minute.tokens.limit}
                            </span>
                            <span className="usage-reset">
                                resets in {formatDuration(
                                    remainingSeconds(llmStatus.checked_at, llmStatus.per_minute.tokens.reset_in_seconds)
                                ) ?? llmStatus.per_minute.tokens.reset_in}
                            </span>
                        </div>
                    ) : (
                        <p className="usage-empty">
                            No data yet — send a chat message first.
                        </p>
                    )}

                    {llmStatus?.per_minute?.requests && (
                        <div className="usage-row">
                            <span className="usage-label">Requests / min</span>
                            <span className="usage-value">
                                {llmStatus.per_minute.requests.remaining} / {llmStatus.per_minute.requests.limit}
                            </span>
                            <span className="usage-reset">
                                resets in {formatDuration(
                                    remainingSeconds(llmStatus.checked_at, llmStatus.per_minute.requests.reset_in_seconds)
                                ) ?? llmStatus.per_minute.requests.reset_in}
                            </span>
                        </div>
                    )}

                    <div className="usage-row">
                        <span className="usage-label">Daily quota</span>
                        {llmStatus?.daily?.known ? (
                            <>
                                <span className="usage-value">
                                    {llmStatus.daily.used} / {llmStatus.daily.limit}
                                </span>
                                <span className="usage-reset">
                                    retry in {formatDuration(
                                        remainingSeconds(llmStatus.daily.hit_at, llmStatus.daily.retry_after_seconds)
                                    )} (last hit {new Date(llmStatus.daily.hit_at).toLocaleTimeString()})
                                </span>
                            </>
                        ) : (
                            <span className="usage-reset">
                                not hit yet this session
                            </span>
                        )}
                    </div>
                </div>

                <div className="settings-actions">
                    <button
                        className="settings-action-btn"
                        onClick={() => {
                            navigate("/upload");
                            onClose();
                        }}
                    >
                        <Icon name="upload" size={15} />
                        Upload Documents
                    </button>
                </div>

                <div className="settings-danger">
                    <p className="settings-danger-label">
                        Danger Zone
                    </p>
                    <button
                        className="settings-danger-btn"
                        onClick={handleClearHistory}
                    >
                        Clear All Chat History
                    </button>
                </div>
            </div>
        </div>
    );
}

export default SettingsModal;
