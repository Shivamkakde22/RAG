const paths = {
    book: (
        <path d="M3 4.5A1.5 1.5 0 0 1 4.5 3H10a3 3 0 0 1 3 3v15a2.5 2.5 0 0 0-2.5-2.5H3.5a.5.5 0 0 1-.5-.5Z M21 4.5A1.5 1.5 0 0 0 19.5 3H14a3 3 0 0 0-3 3v15a2.5 2.5 0 0 1 2.5-2.5h6.5a.5.5 0 0 0 .5-.5Z" />
    ),
    menu: (
        <>
            <line x1="4" y1="7" x2="20" y2="7" />
            <line x1="4" y1="12" x2="20" y2="12" />
            <line x1="4" y1="17" x2="20" y2="17" />
        </>
    ),
    plus: (
        <>
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
        </>
    ),
    search: (
        <>
            <circle cx="11" cy="11" r="7" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </>
    ),
    sliders: (
        <>
            <line x1="4" y1="6" x2="20" y2="6" />
            <circle cx="9" cy="6" r="1.8" />
            <line x1="4" y1="12" x2="20" y2="12" />
            <circle cx="15" cy="12" r="1.8" />
            <line x1="4" y1="18" x2="20" y2="18" />
            <circle cx="11" cy="18" r="1.8" />
        </>
    ),
    sun: (
        <>
            <circle cx="12" cy="12" r="4" />
            <line x1="12" y1="1.5" x2="12" y2="4" />
            <line x1="12" y1="20" x2="12" y2="22.5" />
            <line x1="4.5" y1="4.5" x2="6.2" y2="6.2" />
            <line x1="17.8" y1="17.8" x2="19.5" y2="19.5" />
            <line x1="1.5" y1="12" x2="4" y2="12" />
            <line x1="20" y1="12" x2="22.5" y2="12" />
            <line x1="4.5" y1="19.5" x2="6.2" y2="17.8" />
            <line x1="17.8" y1="6.2" x2="19.5" y2="4.5" />
        </>
    ),
    moon: (
        <path d="M20 12.5A8 8 0 1 1 11.5 4a6.5 6.5 0 0 0 8.5 8.5Z" />
    ),
    message: (
        <path d="M4 4h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9l-4 4v-4H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" />
    ),
    upload: (
        <>
            <polyline points="7 8 12 3 17 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
            <path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4" />
        </>
    ),
    file: (
        <>
            <path d="M6 2h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Z" />
            <path d="M15 2v5h5" />
        </>
    ),
    "file-text": (
        <>
            <path d="M6 2h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1Z" />
            <path d="M15 2v5h5" />
            <line x1="8" y1="13" x2="16" y2="13" />
            <line x1="8" y1="17" x2="16" y2="17" />
        </>
    ),
    trash: (
        <>
            <line x1="3" y1="6" x2="21" y2="6" />
            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
            <line x1="10" y1="11" x2="10" y2="17" />
            <line x1="14" y1="11" x2="14" y2="17" />
        </>
    ),
    x: (
        <>
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
        </>
    ),
    pencil: (
        <>
            <path d="M12 20h9" />
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z" />
        </>
    ),
    copy: (
        <>
            <rect x="9" y="9" width="13" height="13" rx="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
        </>
    ),
    check: (
        <polyline points="20 6 9 17 4 12" />
    ),
    refresh: (
        <>
            <path d="M23 4v6h-6" />
            <path d="M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10" />
            <path d="M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
        </>
    ),
    "bar-chart": (
        <>
            <line x1="6" y1="20" x2="6" y2="14" />
            <line x1="12" y1="20" x2="12" y2="8" />
            <line x1="18" y1="20" x2="18" y2="4" />
        </>
    ),
    send: (
        <>
            <line x1="12" y1="19" x2="12" y2="5" />
            <polyline points="5 12 12 5 19 12" />
        </>
    ),
    square: (
        <rect x="6" y="6" width="12" height="12" rx="1.5" />
    ),
    bot: (
        <>
            <rect x="3" y="8" width="18" height="12" rx="2.5" />
            <circle cx="8.5" cy="14" r="1.5" />
            <circle cx="15.5" cy="14" r="1.5" />
            <line x1="12" y1="8" x2="12" y2="4" />
            <circle cx="12" cy="3" r="1" />
        </>
    ),
    user: (
        <>
            <circle cx="12" cy="8" r="4" />
            <path d="M4 21v-1a8 8 0 0 1 16 0v1" />
        </>
    ),
    "chevron-left": (
        <polyline points="15 18 9 12 15 6" />
    ),
    "chevron-right": (
        <polyline points="9 18 15 12 9 6" />
    ),
    clock: (
        <>
            <circle cx="12" cy="12" r="9" />
            <polyline points="12 7 12 12 16 14" />
        </>
    ),
};

function Icon({ name, size = 18, className = "", strokeWidth = 2 }) {
    const content = paths[name];
    if (!content) return null;

    return (
        <svg
            className={`icon icon-${name} ${className}`}
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            {content}
        </svg>
    );
}

export default Icon;
