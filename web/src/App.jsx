import { HashRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ResultPage from "./pages/ResultPage";
import DetailPage from "./pages/DetailPage";
import "./App.css";

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/results" element={<ResultPage />} />
        <Route path="/restaurants/:id" element={<DetailPage />} />
      </Routes>
    </HashRouter>
  );
}

export default App;
