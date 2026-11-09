/* Rede Farmácia — comportamento do cliente */
(function () {
  "use strict";

  // Registro do service worker (PWA)
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function (err) {
        console.warn("Falha ao registrar o service worker:", err);
      });
    });
  }

  // Botão "Instalar app" quando o navegador oferecer
  var eventoInstalar = null;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    eventoInstalar = e;
    document.querySelectorAll(".instalar-app").forEach(function (el) { el.classList.add("visivel"); });
  });
  document.addEventListener("click", function (e) {
    var botao = e.target.closest(".instalar-app");
    if (!botao || !eventoInstalar) return;
    eventoInstalar.prompt();
    eventoInstalar.userChoice.finally(function () {
      eventoInstalar = null;
      document.querySelectorAll(".instalar-app").forEach(function (el) { el.classList.remove("visivel"); });
    });
  });

  // Confirmação para ações destrutivas: <form data-confirmar="Tem certeza?">
  document.addEventListener("submit", function (e) {
    var msg = e.target.getAttribute("data-confirmar");
    if (msg && !window.confirm(msg)) e.preventDefault();
  }, true);

  // Chat: rola até o fim ao abrir e quando chegam mensagens novas
  function rolarChat(forcar) {
    var caixa = document.getElementById("chat-mensagens");
    if (!caixa) return;
    var pertoDoFim = caixa.scrollHeight - caixa.scrollTop - caixa.clientHeight < 150;
    if (forcar || pertoDoFim) caixa.scrollTop = caixa.scrollHeight;
  }
  document.addEventListener("DOMContentLoaded", function () { rolarChat(true); });
  document.addEventListener("htmx:afterSwap", function (e) {
    if (e.target && e.target.closest && e.target.closest("#chat-mensagens")) rolarChat(false);
  });
  document.addEventListener("htmx:oobAfterSwap", function () { rolarChat(false); });

  // Chat: Enter envia, Shift+Enter quebra linha
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" || e.shiftKey || e.isComposing) return;
    var campo = e.target;
    if (!campo.matches || !campo.matches("#chat-form textarea")) return;
    e.preventDefault();
    if (campo.value.trim()) campo.form.requestSubmit();
  });
  document.addEventListener("htmx:afterRequest", function (e) {
    if (e.detail.elt && e.detail.elt.id === "chat-form" && e.detail.successful) {
      e.detail.elt.reset();
      var campo = e.detail.elt.querySelector("textarea");
      if (campo) campo.focus();
      rolarChat(true);
    }
  });

  // Mostra/oculta a escolha de destinatários/responsável conforme o tipo
  function alternarDependentes() {
    document.querySelectorAll("[data-mostrar-se]").forEach(function (bloco) {
      var partes = bloco.getAttribute("data-mostrar-se").split("=");
      var marcado = document.querySelector('input[name="' + partes[0] + '"]:checked');
      bloco.hidden = !marcado || marcado.value !== partes[1];
    });
  }
  document.addEventListener("change", alternarDependentes);
  document.addEventListener("DOMContentLoaded", alternarDependentes);
})();
