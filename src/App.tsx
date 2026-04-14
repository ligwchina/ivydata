import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import BaseData from "@/pages/BaseData";
import KlineData from "@/pages/KlineData";

export default function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/base-data" element={<BaseData />} />
          <Route path="/kline-data" element={<KlineData />} />
        </Routes>
      </Layout>
    </Router>
  );
}
