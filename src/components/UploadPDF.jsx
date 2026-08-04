import { useState } from "react";
import api from "../api/api";
import Icon from "./Icon";

function UploadPDF({
    documents,
    setDocuments,
    collectionId,
    onUploaded
}) {

    const [file,setFile] = useState(null);

    const [loading,setLoading] = useState(false);

    const [uploadProgress, setUploadProgress] = useState(0);

    const [processingProgress, setProcessingProgress] = useState(null);

    const pollProcessing = (documentId, fileName) => {
        return new Promise((resolve) => {
            const interval = setInterval(async () => {
                try {
                    const response = await api.get(`/documents/${documentId}`);
                    const doc = response.data;
                    const percent = doc.total_chunks
                        ? Math.round((doc.processed_chunks / doc.total_chunks) * 100)
                        : 0;
                    setProcessingProgress(percent);

                    setDocuments(prev =>
                        prev.map(d =>
                            d.id === documentId
                                ? {
                                    ...d,
                                    status: doc.status,
                                    total_chunks: doc.total_chunks,
                                    processed_chunks: doc.processed_chunks
                                }
                                : d
                        )
                    );

                    if (doc.status === "ready" || doc.status === "failed") {
                        clearInterval(interval);
                        resolve(doc.status);
                    }
                } catch (error) {
                    console.log(error);
                    clearInterval(interval);
                    resolve("failed");
                }
            }, 800);
        });
    };

    const uploadFile = async () => {
        if (!file) {
            alert(
                "Please select a PDF or Word document"
            );
            return;
        }
        if (
            file.size >
            100 * 1024 * 1024
        ) {
            alert(
                "File size must be less than 100 MB"
            );
            return;
        }
        const formData = new FormData();
        formData.append(
            "file",
            file
        );
        if (collectionId) {
            formData.append(
                "collection_id",
                collectionId
            );
        }
        setLoading(true);
        setUploadProgress(0);

        try {
            const response = await api.post(
                "/upload",
                formData,
                {
                    headers: {
                        "Content-Type":
                        "multipart/form-data"
                    },
                    onUploadProgress: (event) => {
                        if (!event.total) {
                            return;
                        }
                        const percent = Math.round(
                            (event.loaded / event.total) * 100
                        );
                        setUploadProgress(percent);
                    }
                }
            );

            const documentId = response.data.document_id;

            const newDoc = {
                id: documentId,
                file_name: response.data.file_name,
                total_chunks: response.data.total_chunks,
                processed_chunks: 0,
                status: "pending",
                collection_id: collectionId || null
            };
            setDocuments(
                prev =>
                [
                    ...prev,
                    newDoc
                ]
            );

            setProcessingProgress(0);
            const finalStatus = await pollProcessing(documentId, response.data.file_name);

            setFile(null);
            if (finalStatus === "ready") {
                alert(
                    "Document Uploaded Successfully"
                );
            } else {
                alert(
                    "Document processing failed"
                );
            }
            onUploaded?.();
        }
        catch (error) {
            console.log(error);
            alert(
                error.response?.data?.error
                ||
                "Upload Failed"
            );
        }

        finally {
            setLoading(false);
            setUploadProgress(0);
            setProcessingProgress(null);
        }
    };

    return (
        <div className="upload-card">
            <div className="upload-header">
                <h2>
                    Upload Document
                </h2>
                <p>
                    Upload a PDF or Word document and chat with it
                </p>
            </div>
            <label
                className="upload-box"
            >
                <input
                    type="file"
                    accept=".pdf,.docx"
                    hidden
                    onChange={(e) =>
                        setFile(
                            e.target.files[0]
                        )
                    }
                />
                <div className="upload-icon">
                    <Icon name="upload" size={26} />
                </div>
                {
                    file
                    ?
                    (
                        <>
                            <h4>
                                {
                                    file.name
                                }
                            </h4>
                            <p>
                                {
                                    (
                                        file.size
                                        /
                                        1024
                                        /
                                        1024
                                    ).toFixed(2)
                                }
                                MB
                            </p>
                        </>
                    )
                    :
                    (
                        <>
                            <h4>
                                Choose PDF or Word File
                            </h4>
                            <p>
                                Max Size 100 MB
                            </p>
                        </>
                    )
                }

            </label>

            {
                loading &&
                <div className="upload-progress">
                    <div
                        className="upload-progress-bar"
                        style={{
                            width: `${uploadProgress < 100 ? uploadProgress : (processingProgress ?? 0)}%`
                        }}
                    ></div>
                </div>
            }

            <button
                className="upload-btn"
                onClick={uploadFile}
                disabled={loading}
            >
                {
                    !loading
                    ?
                    "Upload Document"
                    :
                    uploadProgress < 100
                    ?
                    `Uploading... ${uploadProgress}%`
                    :
                    `Processing... ${processingProgress ?? 0}%`
                }
            </button>
        </div>
    );
}
export default UploadPDF;