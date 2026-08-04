import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Icon from "./Icon";

function formatRelativeDate(isoString) {
    const date = new Date(isoString);
    const diffDays = Math.floor(
        (new Date() - date) / 86400000
    );

    if (diffDays === 0) {
        return date.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
        });
    }
    if (diffDays === 1) {
        return "Yesterday";
    }
    if (diffDays < 7) {
        return `${diffDays} days ago`;
    }
    return date.toLocaleDateString();
}

function Sidebar({
    sessions,
    currentSessionId,
    setCurrentSessionId,
    onNewChat,
    theme,
    onToggleTheme,
    onOpenSettings,
    mobileOpen,
    setMobileOpen
}) {
    const [collapsed, setCollapsed] = useState(false);
    const [search, setSearch] = useState("");
    const navigate = useNavigate();

    const filteredSessions = sessions.filter((session) =>
        session.title.toLowerCase().includes(search.toLowerCase())
    );

    const closeMobile = () => setMobileOpen(false);

    return (
        <>
        {
            mobileOpen &&
            <div
                className="mobile-sidebar-backdrop"
                onClick={closeMobile}
            ></div>
        }
        <div
            className={
                (collapsed ? "sidebar collapsed" : "sidebar")
                +
                (mobileOpen ? " mobile-open" : "")
            }
        >
            <div className="sidebar-header">
                <div className="sidebar-header-top">
                    <div className="sidebar-logo">
                        <Icon name="book" size={20} />
                        <span className="label">DocMind</span>
                    </div>
                    <button
                        className="sidebar-toggle"
                        onClick={() =>
                            setCollapsed(prev => !prev)
                        }
                        title={
                            collapsed
                            ? "Expand sidebar"
                            : "Collapse sidebar"
                        }
                    >
                        <Icon name={collapsed ? "chevron-right" : "chevron-left"} size={15} />
                    </button>
                </div>

                <button
                    className="new-chat-btn"
                    onClick={() => {
                        onNewChat();
                        navigate("/");
                        closeMobile();
                    }}
                    title="New Chat"
                >
                    <Icon name="plus" size={16} />
                    <span className="label">New Chat</span>
                </button>

                <div className="sidebar-search">
                    <input
                        type="text"
                        className="sidebar-search-input"
                        placeholder="Search chats..."
                        value={search}
                        onChange={(e) =>
                            setSearch(e.target.value)
                        }
                    />
                </div>
            </div>

            <div className="sidebar-scroll">

                <div className="sidebar-section">
                    <div className="sidebar-section-header">
                        <span className="label">
                            Recent Chats
                        </span>
                    </div>
                    {
                        filteredSessions.length === 0
                        &&
                        <div className="empty-sidebar">
                            <div className="empty-icon">
                                <Icon name="message" size={26} />
                            </div>
                            <p>
                                No conversations yet
                            </p>
                        </div>
                    }
                    {
                        filteredSessions.map(
                            (session) => (
                                <div
                                    key={session.id}
                                    className={
                                        session.id === currentSessionId
                                        ?
                                        "session-item active"
                                        :
                                        "session-item"
                                    }
                                    title={session.title}
                                    onClick={() => {
                                        setCurrentSessionId(
                                            session.id
                                        );
                                        navigate("/");
                                        closeMobile();
                                    }}
                                >
                                    <div
                                        className="session-title"
                                    >
                                        {
                                            session.title
                                        }
                                    </div>
                                    <div
                                        className="session-meta"
                                    >
                                        {
                                            formatRelativeDate(
                                                session.created_at
                                            )
                                        }
                                    </div>
                                </div>
                            )
                        )
                    }
                </div>

            </div>

            <div className="sidebar-footer">
                <Link
                    to="/search"
                    className="sidebar-footer-btn"
                    title="Search Documents"
                    onClick={closeMobile}
                >
                    <Icon name="search" size={15} />
                    <span className="label">Search</span>
                </Link>
                <button
                    className="sidebar-footer-btn"
                    title="Settings"
                    onClick={() => {
                        onOpenSettings();
                        closeMobile();
                    }}
                >
                    <Icon name="sliders" size={15} />
                    <span className="label">Settings</span>
                </button>
                <button
                    className="sidebar-footer-btn"
                    title={
                        theme === "dark"
                        ? "Switch to light mode"
                        : "Switch to dark mode"
                    }
                    onClick={onToggleTheme}
                >
                    <Icon name={theme === "dark" ? "sun" : "moon"} size={15} />
                    <span className="label">
                        {
                            theme === "dark"
                            ? "Light Mode"
                            : "Dark Mode"
                        }
                    </span>
                </button>
            </div>
        </div>
        </>
    );
}
export default Sidebar;
