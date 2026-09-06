import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import DatasetsPage from "./pages/DatasetsPage";
import CollectPage from "./pages/CollectPage";
import ShowcasePage from "./pages/ShowcasePage";
import AuditPage from "./pages/AuditPage";
import SourcesPage from "./pages/SourcesPage";
import QueryPage from "./pages/QueryPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/datasets" replace />} />
          <Route path="datasets" element={<DatasetsPage />} />
          <Route path="collect" element={<CollectPage />} />
          <Route path="showcase" element={<ShowcasePage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="sources" element={<SourcesPage />} />
          <Route path="query" element={<QueryPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
