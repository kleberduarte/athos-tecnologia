// CRM Funil — drag-and-drop de oportunidades entre estágios

const getCsrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content ?? '';

document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".card");
  const columnBodies = document.querySelectorAll(".column-body");

  let cardArrastado = null;
  let arrastando = false;

  cards.forEach((card) => {
    card.setAttribute("draggable", "true");

    card.addEventListener("dragstart", () => {
      cardArrastado = card;
      arrastando = true;
      card.classList.add("dragging");
    });

    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
      cardArrastado = null;
      setTimeout(() => { arrastando = false; }, 50);
    });

    card.addEventListener("click", () => {
      if (!arrastando) {
        window.location.href = `/crm/oportunidade/${card.dataset.id}`;
      }
    });
  });

  columnBodies.forEach((body) => {
    const coluna = body.closest(".column");

    body.addEventListener("dragover", (e) => {
      e.preventDefault();
      coluna.classList.add("drag-over");
    });

    body.addEventListener("dragleave", () => {
      coluna.classList.remove("drag-over");
    });

    body.addEventListener("drop", async (e) => {
      e.preventDefault();
      coluna.classList.remove("drag-over");
      if (!cardArrastado) return;

      const novoEstagio = body.dataset.estagio;
      const opId = cardArrastado.dataset.id;
      const colunaOrigemBody = cardArrastado.closest(".column-body");

      if (colunaOrigemBody === body) return;

      body.appendChild(cardArrastado);
      atualizarContadores();

      try {
        const resp = await fetch(`/crm/oportunidade/${opId}/estagio`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify({ estagio: novoEstagio }),
        });
        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          throw new Error(data.erro || "Falha ao atualizar estágio");
        }
        // Sucesso — não precisa recarregar, o card já foi movido no DOM
      } catch (err) {
        alert(`Não foi possível mover a oportunidade: ${err.message}`);
        window.location.reload();
      }
    });
  });

  function atualizarContadores() {
    document.querySelectorAll(".column").forEach((coluna) => {
      const count = coluna.querySelectorAll(".card").length;
      const countEl = coluna.querySelector(".col-count");
      if (countEl) countEl.textContent = count;
    });
  }
});
