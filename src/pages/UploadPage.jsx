import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/api";
import UploadPDF from "../components/UploadPDF";
import Icon from "../components/Icon";

function UploadPage({
    documents,
    setDocuments,
    collections,
    onCreateCollection,
    activeDocumentId,
    setActiveDocumentId
}) {
    const [collectionId, setCollectionId] = useState("");
    const [creatingNew, setCreatingNew] = useState(false);
    const [newCollectionName, setNewCollectionName] = useState("");

    const handleSelectChange = (e) => {
        if (e.target.value === "__new__") {
            setCreatingNew(true);
        } else {
            setCreatingNew(false);
            setCollectionId(e.target.value);
        }
    };

    const handleCreateCollection = async () => {
        if (!newCollectionName.trim()) {
            return;
        }
        try {
            const response = await api.post("/collections", {
                name: newCollectionName.trim()
            });
            onCreateCollection(response.data);
            setCollectionId(String(response.data.id));
            setCreatingNew(false);
            setNewCollectionName("");
        } catch (error) {
            console.log(error);
            alert("Could not create collection");
        }
    };

    const handleDeleteDocument = async (e, doc) => {
        e.stopPropagation();

        const ok = window.confirm(
            `Delete "${doc.file_name}"? This can't be undone.`
        );
        if (!ok) {
            return;
        }

        try {
            await api.delete(`/documents/${doc.id}`);

            setDocuments(
                prev => prev.filter(d => d.id !== doc.id)
            );

            if (activeDocumentId === doc.id) {
                setActiveDocumentId(null);
            }
        } catch (error) {
            console.log(error);
            alert("Could not delete document");
        }
    };

    return (
        <div className="upload-page">
            <div className="documents-sidebar">
                <h3 className="documents-sidebar-heading">
                    <Icon name="file" size={14} /> Your Documents
                </h3>
                <p className="documents-sidebar-hint">
                    Click a file to scope chat to just that document.
                </p>
                <div className="document-list">
                    {
                        documents.length === 0
                        &&
                        <div className="empty-sidebar">
                            <div className="empty-icon">
                                <Icon name="file" size={26} />
                            </div>
                            <p>
                                No PDF Uploaded
                            </p>
                        </div>
                    }
                    {
                        documents.map(
                            (doc) => (
                                <div
                                    key={doc.id}
                                    className={
                                        doc.id === activeDocumentId
                                        ?
                                        "doc-item active"
                                        :
                                        "doc-item"
                                    }
                                    title={doc.file_name}
                                    onClick={() =>
                                        setActiveDocumentId(
                                            prev =>
                                                prev === doc.id
                                                ? null
                                                : doc.id
                                        )
                                    }
                                >
                                    <div
                                        className="doc-icon"
                                    >
                                        <Icon
                                            name={
                                                doc.file_name.toLowerCase().endsWith(".docx")
                                                ? "file-text"
                                                : "file"
                                            }
                                            size={18}
                                        />
                                    </div>
                                    <div
                                        className="doc-info"
                                    >
                                        <div
                                            className="doc-name"
                                        >
                                            {
                                                doc.file_name
                                            }
                                        </div>
                                        <div
                                            className="doc-meta"
                                        >
                                            <span
                                                className={
                                                    `doc-status-dot status-${doc.status || "ready"}`
                                                }
                                            ></span>
                                            {
                                                doc.status === "pending"
                                                ?
                                                `${doc.processed_chunks ?? 0}/${doc.total_chunks || "?"}`
                                                :
                                                doc.total_chunks
                                            }
                                            {" "}
                                            Chunks
                                        </div>
                                    </div>
                                    <button
                                        className="doc-delete-btn"
                                        title="Delete document"
                                        onClick={(e) =>
                                            handleDeleteDocument(e, doc)
                                        }
                                    >
                                        <Icon name="trash" size={14} />
                                    </button>
                                </div>
                            )
                        )
                    }
                </div>
            </div>
            <div className="upload-main">
                <div className="upload-page-card">
                    <Link
                        to="/"
                        className="back-to-chat"
                    >
                        <Icon name="chevron-left" size={14} /> Back to Chat
                    </Link>

                    {
                        activeDocumentId &&
                        <div className="active-filter-badge upload-active-filter">
                            <span className="active-filter-name">
                                Filtering: {
                                    documents.find(
                                        (d) => d.id === activeDocumentId
                                    )?.file_name
                                    ||
                                    "1 document"
                                }
                            </span>
                            <button
                                className="active-filter-clear"
                                onClick={() => setActiveDocumentId(null)}
                                title="Clear filter"
                            >
                                <Icon name="x" size={14} />
                            </button>
                        </div>
                    }

                    <div className="collection-picker">
                        <label className="collection-picker-label">
                            Collection
                        </label>
                        <select
                            className="collection-select"
                            value={creatingNew ? "__new__" : collectionId}
                            onChange={handleSelectChange}
                        >
                            <option value="">No Collection</option>
                            {
                                collections.map((c) => (
                                    <option
                                        key={c.id}
                                        value={c.id}
                                    >
                                        {c.name}
                                    </option>
                                ))
                            }
                            <option value="__new__">
                                + Create New Collection...
                            </option>
                        </select>

                        {
                            creatingNew &&
                            <div className="new-collection-row">
                                <input
                                    type="text"
                                    className="new-collection-input"
                                    placeholder="Collection name"
                                    value={newCollectionName}
                                    onChange={(e) =>
                                        setNewCollectionName(e.target.value)
                                    }
                                />
                                <button
                                    className="new-collection-create-btn"
                                    onClick={handleCreateCollection}
                                >
                                    Create
                                </button>
                            </div>
                        }
                    </div>

                    <UploadPDF
                        documents={documents}
                        setDocuments={setDocuments}
                        collectionId={collectionId || null}
                    />
                </div>
            </div>
        </div>
    );
}

export default UploadPage;
