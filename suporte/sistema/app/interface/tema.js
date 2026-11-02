/* Tema antes da pintura; armazenamento desabilitado não impede a interface. */
(function () {
  'use strict';
  var tema = 'sistema';
  try { tema = window.localStorage.getItem('rodovia_tema') || tema; } catch (_) {}
  if (tema === 'sistema') {
    tema = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'escuro' : 'claro';
  }
  document.documentElement.dataset.tema = tema === 'claro' ? 'claro' : 'escuro';
}());
