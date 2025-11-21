import { Routes, Route } from 'react-router-dom';
import Home from './Home';
import DimensionExtractor from './DimensionExtractor';
import CAE from './CAE';
import StructuralAnalysis from './components/analysis/StructuralAnalysis';
import ThermalAnalysis from './components/analysis/ThermalAnalysis';
import MagnetostaticAnalysis from './components/analysis/MagnetostaticAnalysis';
import ModalAnalysis from './components/analysis/ModalAnalysis';
import AIRecommendation from './components/analysis/AIRecommendation';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/modelling" element={<DimensionExtractor />} />
      <Route path="/cae" element={<CAE />} />
      <Route path="/cae/ai-recommend" element={<AIRecommendation />} />
      <Route path="/cae/structural" element={<StructuralAnalysis />} />
      <Route path="/cae/thermal" element={<ThermalAnalysis />} />
      <Route path="/cae/magnetostatic" element={<MagnetostaticAnalysis />} />
      <Route path="/cae/modal" element={<ModalAnalysis />} />
    </Routes>
  );
}

export default App;
