import ReactMarkdown from "react-markdown";
import Icon from "./Icon";

const QUERY_TYPE_LABEL = {
    simple: null,
    summarization: "Summary",
    multi_part: "Multi-part",
    out_of_scope: "Out of scope",
};

function normalizeBullets(text) {
    if (!text) return text;
    return text.replace(/\s*•\s*/g, "\n- ").trim();
}

function ScoreBar({ label, score }) {
    const pct = Math.round(score * 100);
    const color =
        pct >= 70 ? "var(--status-ready)" :
        pct >= 40 ? "var(--status-pending)" :
        "var(--status-failed)";

    return (
        <div className="ragas-score-row">
            <span className="ragas-score-label">{label}</span>
            <div className="ragas-bar-track">
                <div
                    className="ragas-bar-fill"
                    style={{ width: `${pct}%`, background: color }}
                />
            </div>
            <span className="ragas-score-pct" style={{ color }}>{pct}%</span>
        </div>
    );
}

function Message({
    role,
    content,
    queryType,
    copied,
    onCopy,
    onRegenerate,
    onEdit,
    onEvaluate,
    evalScore,
    evalLoading
}) {
    const isUser = role === "user";
    const typeLabel = QUERY_TYPE_LABEL[queryType];

    return (
        <div className={`msg-row ${isUser ? "msg-user" : "msg-assistant"}`}>
            <div className="msg-meta">
                <span className="msg-sender">
                    <Icon name={isUser ? "user" : "bot"} size={13} />
                    {isUser ? "You" : "DocMind"}
                </span>
                {!isUser && typeLabel && (
                    <span className="query-type-badge">{typeLabel}</span>
                )}
            </div>

            <div className="msg-content">
                {isUser ? (
                    content
                ) : (
                    <ReactMarkdown>{normalizeBullets(content)}</ReactMarkdown>
                )}
            </div>

            <div className="message-actions">
                <button
                    className="message-action-btn"
                    onClick={onCopy}
                    title="Copy"
                >
                    <Icon name={copied ? "check" : "copy"} size={13} />
                    {copied ? "Copied" : "Copy"}
                </button>
                {onRegenerate && (
                    <button
                        className="message-action-btn"
                        onClick={onRegenerate}
                        title="Regenerate response"
                    >
                        <Icon name="refresh" size={13} />
                        Regenerate
                    </button>
                )}
                {onEdit && (
                    <button
                        className="message-action-btn"
                        onClick={onEdit}
                        title="Edit and resend"
                    >
                        <Icon name="pencil" size={13} />
                        Edit
                    </button>
                )}
                {onEvaluate && (
                    <button
                        className="message-action-btn"
                        onClick={onEvaluate}
                        disabled={evalLoading}
                        title="Evaluate with RAGAS"
                    >
                        <Icon name={evalLoading ? "clock" : "bar-chart"} size={13} />
                        {evalLoading ? "Evaluating..." : "Evaluate"}
                    </button>
                )}
            </div>

            {evalScore && (
                <div className="ragas-panel">
                    <div className="ragas-panel-title">RAG Quality Scores</div>
                    <ScoreBar label="Faithfulness" score={evalScore.scores.faithfulness} />
                    <ScoreBar label="Context Precision" score={evalScore.scores.context_precision} />
                    <ScoreBar label="Answer Relevancy" score={evalScore.scores.answer_relevancy} />
                    <div className="ragas-divider" />
                    <ScoreBar label="Overall" score={evalScore.scores.overall} />
                    {evalScore.details?.faithfulness && (
                        <p className="ragas-detail">{evalScore.details.faithfulness}</p>
                    )}
                    {evalScore.details?.context_precision && (
                        <p className="ragas-detail">{evalScore.details.context_precision}</p>
                    )}
                </div>
            )}
        </div>
    );
}

export default Message;
