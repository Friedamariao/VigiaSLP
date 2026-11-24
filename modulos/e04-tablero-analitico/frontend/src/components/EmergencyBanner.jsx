import React from 'react';

function EmergencyBanner() {
  return (
    <div className="emergency-banner" role="complementary" aria-label="Números de emergencia">
      <span>Emergencias: <strong>911</strong></span>
      <span className="separator">|</span>
      <span>Denuncia anónima: <strong>089</strong></span>
    </div>
  );
}

export default EmergencyBanner;
