import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import StoryPage from "./pages/StoryPage";
import CoachChat from "./components/CoachChat";
import "./App.css";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/story" element={<StoryPage />} />
          <Route path="/coach" element={<div className="panel"><CoachChat /></div>} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;