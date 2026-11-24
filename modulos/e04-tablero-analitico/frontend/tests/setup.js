import '@testing-library/jest-dom';

globalThis.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

HTMLCanvasElement.prototype.getContext = function () {
  return {
    canvas: this,
    clearRect() {},
    fillRect() {},
    getImageData(x, y, w, h) {
      return { data: new Array(w * h * 4).fill(0) };
    },
    putImageData() {},
    createImageData() { return []; },
    setTransform() {},
    resetTransform() {},
    drawImage() {},
    save() {},
    fillText() {},
    restore() {},
    beginPath() {},
    moveTo() {},
    lineTo() {},
    closePath() {},
    stroke() {},
    translate() {},
    scale() {},
    rotate() {},
    arc() {},
    fill() {},
    measureText() { return { width: 0 }; },
    transform() {},
    rect() {},
    clip() {},
    createLinearGradient() { return { addColorStop() {} }; },
    createRadialGradient() { return { addColorStop() {} }; },
    createPattern() { return {}; },
  };
};
