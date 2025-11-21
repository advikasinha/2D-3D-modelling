import { Routes, Route } from 'react-router-dom';
import Home from './Home';
import DimensionExtractor from './DimensionExtractor';
import CAE from './CAE';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/modelling" element={<DimensionExtractor />} />
      <Route path="/cae" element={<CAE />} />
    </Routes>
  );
}

export default App;
