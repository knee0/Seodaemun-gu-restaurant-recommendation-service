import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import PreferencePage from "./pages/PreferencePage";
import ResultPage from "./pages/ResultPage";
import DetailPage from "./pages/DetailPage";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/preferences" element={<PreferencePage />} />
        <Route path="/results" element={<ResultPage />} />
        <Route path="/restaurants/:id" element={<DetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;