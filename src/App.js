import "./styles/App.css";

import { useState, useEffect } from "react";

import { Routes, Route } from "react-router-dom";

import api from "./api/api";

import Sidebar from "./components/Sidebar";

import ChatWindow from "./components/ChatWindow";

import UploadPage from "./pages/UploadPage";

import SearchPage from "./pages/SearchPage";

import SettingsModal from "./components/SettingsModal";

import Icon from "./components/Icon";


function App() {

    const [

        documents,

        setDocuments

    ] = useState([]);


    const [

        sessions,

        setSessions

    ] = useState([]);


    const [

        currentSessionId,

        setCurrentSessionId

    ] = useState(null);


    const [

        collections,

        setCollections

    ] = useState([]);


    const [

        activeDocumentId,

        setActiveDocumentId

    ] = useState(null);


    const [

        theme,

        setTheme

    ] = useState(
        () => localStorage.getItem("theme") || "dark"
    );


    const [

        settingsOpen,

        setSettingsOpen

    ] = useState(false);


    const [

        mobileSidebarOpen,

        setMobileSidebarOpen

    ] = useState(false);


    useEffect(() => {

        document.documentElement.dataset.theme = theme;
        localStorage.setItem("theme", theme);

    }, [theme]);


    useEffect(() => {

        api.get("/documents").then((response) => {

            const docs = response.data.documents.map((doc) => ({
                id: doc.id,
                file_name: doc.file_name,
                total_chunks: doc.total_chunks,
                status: doc.status,
                collection_id: doc.collection_id
            }));

            setDocuments(docs);
        }).catch((error) => {
            console.log(error);
        });

    }, []);


    const refreshCollections = () => {

        api.get("/collections").then((response) => {
            setCollections(response.data);
        }).catch((error) => {
            console.log(error);
        });
    };


    useEffect(() => {

        refreshCollections();

    }, []);


    const refreshSessions = () => {

        api.get("/sessions").then((response) => {
            setSessions(response.data);
        }).catch((error) => {
            console.log(error);
        });
    };


    useEffect(() => {

        refreshSessions();

    }, []);



    return (

        <div className="app-layout">


            <button
                className="mobile-menu-btn"
                onClick={() => setMobileSidebarOpen(true)}
                title="Open menu"
            >
                <Icon name="menu" size={18} />
            </button>


            <Sidebar

                sessions={sessions}

                currentSessionId={currentSessionId}

                setCurrentSessionId={setCurrentSessionId}

                onNewChat={() => setCurrentSessionId(null)}

                theme={theme}

                onToggleTheme={() =>
                    setTheme(t => t === "dark" ? "light" : "dark")
                }

                onOpenSettings={() => setSettingsOpen(true)}

                mobileOpen={mobileSidebarOpen}

                setMobileOpen={setMobileSidebarOpen}

            />


            <div className="main-content">

                <Routes>

                    <Route
                        path="/"
                        element={
                            <ChatWindow

                                currentSessionId={currentSessionId}

                                setCurrentSessionId={setCurrentSessionId}

                                onSessionCreated={refreshSessions}

                                activeDocumentId={activeDocumentId}

                                setActiveDocumentId={setActiveDocumentId}

                                documents={documents}

                            />
                        }
                    />

                    <Route
                        path="/upload"
                        element={
                            <UploadPage

                                documents={documents}

                                setDocuments={setDocuments}

                                collections={collections}

                                onCreateCollection={(newCollection) =>
                                    setCollections(prev => [newCollection, ...prev])
                                }

                                activeDocumentId={activeDocumentId}

                                setActiveDocumentId={setActiveDocumentId}

                            />
                        }
                    />

                    <Route
                        path="/search"
                        element={
                            <SearchPage

                                setActiveDocumentId={setActiveDocumentId}

                            />
                        }
                    />

                </Routes>

            </div>


            {
                settingsOpen &&
                <SettingsModal

                    documents={documents}

                    sessions={sessions}

                    onClearHistory={() => {
                        setSessions([]);
                        setCurrentSessionId(null);
                        setSettingsOpen(false);
                    }}

                    onClose={() => setSettingsOpen(false)}

                />
            }


        </div>

    );

}


export default App;
