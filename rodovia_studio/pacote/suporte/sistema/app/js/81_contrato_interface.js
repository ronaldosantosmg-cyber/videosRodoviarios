/* Contrato de apresentação: usa comandos existentes; não dispara cálculos ou polling. */
(function () {
  'use strict';
  document.addEventListener('click', function (event) {
    const button = event.target.closest('[data-dialog-close]');
    if (!button) return;
    const dialog = button.closest('dialog');
    if (dialog && typeof dialog.close === 'function') dialog.close();
  });
  const required = ['canvas', 'projects', 'name', 'traffic_density', 'render', 'preview', 'menuBar'];
  const missing = required.filter(id => !document.getElementById(id));
  const capabilities = {
    canvas2d: !!window.CanvasRenderingContext2D,
    webgl: !!(window.WebGL2RenderingContext || window.WebGLRenderingContext),
    dialog: typeof window.HTMLDialogElement !== 'undefined',
    pointer: typeof window.PointerEvent !== 'undefined',
    resizeObserver: typeof window.ResizeObserver !== 'undefined'
  };
  let notice = document.getElementById('rsInterfaceNotice');
  if (!notice) {
    notice = document.createElement('p');
    notice.id = 'rsInterfaceNotice';
    notice.setAttribute('role', 'status');
    notice.hidden = true;
    document.querySelector('main').before(notice);
  }
  function announce(text) { notice.textContent = text; notice.hidden = false; }
  if (missing.length) announce('Interface incompleta: ' + missing.join(', ') + '. Verifique a instalação antes de editar.');
  else if (!capabilities.canvas2d || !capabilities.dialog || !capabilities.pointer) {
    announce('Este navegador não oferece todos os recursos de edição. Use uma versão atual do Chrome, Edge ou Firefox.');
  } else if (!capabilities.webgl) {
    announce('WebGL indisponível. Use a visualização 2D; a disponibilidade real do 3D depende também do dispositivo.');
  }
  window.RodoviaInterface = Object.freeze({
    revision: 26,
    capabilities: Object.freeze(capabilities),
    missing: Object.freeze(missing),
    ready: missing.length === 0 && capabilities.canvas2d && capabilities.dialog && capabilities.pointer
  });
  window.dispatchEvent(new CustomEvent('rodovia:interface-ready', { detail: window.RodoviaInterface }));
}());
