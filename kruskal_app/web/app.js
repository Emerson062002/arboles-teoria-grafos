    const ejemploVertices = ["A", "B", "C", "D", "E"];
    const ejemploAristas = [
      { desde: "A", hasta: "B", peso: 4 },
      { desde: "A", hasta: "C", peso: 2 },
      { desde: "B", hasta: "C", peso: 1 },
      { desde: "B", hasta: "D", peso: 5 },
      { desde: "C", hasta: "D", peso: 8 },
      { desde: "C", hasta: "E", peso: 10 },
      { desde: "D", hasta: "E", peso: 2 }
    ];

    let vertices = [...ejemploVertices];
    let aristas = [...ejemploAristas];
    let pasos = [];
    let pasoActual = 0;
    let analisis = null;
    let rotacionX = -0.24;
    let rotacionY = 0.18;
    let arrastrando = false;
    let posicionPuntero = null;
    let inicioPuntero = null;
    let seMovioPuntero = false;
    let posicionesActuales = new Map();
    let verticeSeleccionado = null;
    let ultimoFrame = 0;
    let frameAnimacion = null;
    const canvasGrafo = document.getElementById("graph-canvas");
    const contextoGrafo = canvasGrafo.getContext("2d");
    const preferenciaMovimientoReducido = window.matchMedia("(prefers-reduced-motion: reduce)");
    let giroAutomatico = !preferenciaMovimientoReducido.matches;
    const listaPasos = document.getElementById("steps");
    const botonSiguiente = document.getElementById("next");

    function escaparHtml(valor) {
      return String(valor).replace(/[&<>"']/g, (caracter) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      })[caracter]);
    }

    function claveArista(arista) {
      return JSON.stringify([arista.desde, arista.hasta].sort());
    }

    function dibujarGrafo() {
      const advertencia = document.getElementById("graph-warning");
      const grafoGrande = vertices.length > 12 || aristas.length > 24;
      advertencia.hidden = !grafoGrande;
      advertencia.textContent = grafoGrande
        ? "Este grafo es grande para la vista 3D; algunas conexiones pueden cruzarse."
        : "";
      document.getElementById("graph-count").textContent =
        `${vertices.length} ${vertices.length === 1 ? "vértice" : "vértices"} · ${aristas.length} ${aristas.length === 1 ? "arista" : "aristas"}`;
      canvasGrafo.setAttribute(
        "aria-label",
        `Grafo ponderado 3D con ${vertices.join(", ")}. Haz clic en un punto para ver su explicación; usa las flechas para cambiar de punto y arrastra para girar.`
      );
      actualizarSelectorVertices();
      dibujarEscena3D();
    }

    function actualizarSelectorVertices() {
      const selector = document.getElementById("vertex-picker");
      selector.replaceChildren();
      if (!vertices.includes(verticeSeleccionado)) verticeSeleccionado = null;
      vertices.forEach((vertice) => {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.textContent = vertice;
        boton.setAttribute("aria-label", `Explicar vértice ${vertice}`);
        boton.setAttribute("aria-pressed", String(vertice === verticeSeleccionado));
        boton.addEventListener("click", () => seleccionarVertice(vertice));
        selector.append(boton);
      });
      selector.hidden = vertices.length === 0;
      actualizarExplicacionVertice();
    }

    function seleccionarVertice(vertice) {
      if (!vertices.includes(vertice)) return;
      verticeSeleccionado = vertice;
      document.querySelectorAll("#vertex-picker button").forEach((boton) => {
        boton.setAttribute("aria-pressed", String(boton.textContent === vertice));
      });
      actualizarExplicacionVertice();
      dibujarEscena3D();
    }

    function seleccionarVerticeCercano(x, y) {
      let candidato = null;
      let distanciaMinima = Infinity;
      for (const [vertice, posicion] of posicionesActuales) {
        const distancia = Math.hypot(posicion.x - x, posicion.y - y);
        if (distancia < distanciaMinima) {
          candidato = vertice;
          distanciaMinima = distancia;
        }
      }
      if (candidato !== null && distanciaMinima <= 28) seleccionarVertice(candidato);
    }

    function actualizarExplicacionVertice() {
      const titulo = document.getElementById("vertex-details-title");
      const descripcion = document.getElementById("vertex-details-description");
      const conexiones = document.getElementById("vertex-details-links");
      conexiones.replaceChildren();
      if (verticeSeleccionado === null) {
        titulo.textContent = "Elige un vértice";
        descripcion.textContent = "Haz clic en un nodo 3D o en su nombre para conocer sus conexiones, pesos y decisiones de Kruskal.";
        return;
      }

      const incidentes = aristas
        .map((arista, indice) => ({ arista, indice }))
        .filter(({ arista }) => arista.desde === verticeSeleccionado || arista.hasta === verticeSeleccionado);
      titulo.textContent = `Vértice ${verticeSeleccionado}`;
      descripcion.textContent = incidentes.length
        ? `${verticeSeleccionado} es un punto del grafo con ${incidentes.length} ${incidentes.length === 1 ? "conexión" : "conexiones"}. Cada conexión une este vértice con otro; su peso representa el costo.`
        : `${verticeSeleccionado} es un punto aislado: no tiene conexiones y permanece en su propia componente.`;

      incidentes.forEach(({ arista, indice }) => {
        const otroVertice = arista.desde === verticeSeleccionado ? arista.hasta : arista.desde;
        const indicePaso = pasos.findIndex((paso) => paso.indice === indice);
        let estado = "pending";
        let etiquetaEstado = "pendiente de evaluar";
        if (indicePaso >= 0 && indicePaso < pasoActual) {
          if (pasos[indicePaso].agrega) {
            estado = "added";
            etiquetaEstado = "incluida en el árbol";
          } else {
            estado = "rejected";
            etiquetaEstado = "descartada porque formaría un ciclo";
          }
        } else if (indicePaso < 0) {
          estado = "pending";
          etiquetaEstado = "no evaluada: Kruskal ya no necesitó revisarla";
        }

        const etiqueta = document.createElement("span");
        etiqueta.className = `vertex-link ${estado}`;
        etiqueta.textContent = `${verticeSeleccionado}–${otroVertice} · peso ${arista.peso} · ${etiquetaEstado}`;
        conexiones.append(etiqueta);
      });
    }

    function transformarPunto(punto) {
      const cosenoY = Math.cos(rotacionY);
      const senoY = Math.sin(rotacionY);
      const x = punto.x * cosenoY + punto.z * senoY;
      const zIntermedio = -punto.x * senoY + punto.z * cosenoY;
      const cosenoX = Math.cos(rotacionX);
      const senoX = Math.sin(rotacionX);
      return {
        x,
        y: punto.y * cosenoX - zIntermedio * senoX,
        z: punto.y * senoX + zIntermedio * cosenoX
      };
    }

    function dibujarEscena3D() {
      const ancho = canvasGrafo.clientWidth;
      const alto = canvasGrafo.clientHeight;
      if (!ancho || !alto) return;
      const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
      const anchoInterno = Math.round(ancho * pixelRatio);
      const altoInterno = Math.round(alto * pixelRatio);
      if (canvasGrafo.width !== anchoInterno || canvasGrafo.height !== altoInterno) {
        canvasGrafo.width = anchoInterno;
        canvasGrafo.height = altoInterno;
      }
      contextoGrafo.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
      contextoGrafo.clearRect(0, 0, ancho, alto);

      const radio = Math.min(ancho * 0.37, alto * 0.35, 185);
      const foco = Math.min(ancho, alto) * 1.55;
      const centroX = ancho / 2;
      const centroY = alto / 2 + 5;
      const posiciones = new Map();
      const goldenAngle = Math.PI * (3 - Math.sqrt(5));
      vertices.forEach((vertice, indice) => {
        const y = vertices.length === 1 ? 0 : 1 - (2 * indice) / (vertices.length - 1);
        const radioHorizontal = Math.sqrt(Math.max(0, 1 - y * y));
        const angle = goldenAngle * indice;
        const point = transformarPunto({
          x: Math.cos(angle) * radioHorizontal,
          y,
          z: Math.sin(angle) * radioHorizontal
        });
        const perspective = foco / (foco - point.z * radio * 0.62);
        posiciones.set(vertice, {
          x: centroX + point.x * radio * perspective,
          y: centroY + point.y * radio * perspective,
          z: point.z,
          scale: perspective
        });
      });
      posicionesActuales = posiciones;

      const edgeStates = new Map();
      pasos.slice(0, pasoActual).forEach((paso) => {
        edgeStates.set(paso.indice, paso.agrega ? "selected" : "rejected");
      });
      const puentes = new Set((analisis?.cortaduras?.puentes ?? []).map(claveArista));
      const cuelloBotella = new Set((analisis?.cuello_botella ?? []).map(claveArista));
      const drawEdges = aristas.map((edge, index) => {
        const from = posiciones.get(edge.desde);
        const to = posiciones.get(edge.hasta);
        const key = claveArista(edge);
        return {
          edge, index, from, to, depth: (from.z + to.z) / 2,
          isBridge: puentes.has(key), isBottleneck: cuelloBotella.has(key)
        };
      }).sort((a, b) => a.depth - b.depth);

      contextoGrafo.save();
      contextoGrafo.lineCap = "round";
      for (const item of drawEdges) {
        const state = edgeStates.get(item.index);
        const structuralColor = item.isBottleneck
          ? "#b9aaff"
          : item.isBridge ? "#ffc878" : null;
        const conectaSeleccionado = verticeSeleccionado !== null &&
          (item.edge.desde === verticeSeleccionado || item.edge.hasta === verticeSeleccionado);
        const depthOpacity = 0.3 + ((item.depth + 1) / 2) * 0.5;
        contextoGrafo.beginPath();
        contextoGrafo.moveTo(item.from.x, item.from.y);
        contextoGrafo.lineTo(item.to.x, item.to.y);
        contextoGrafo.setLineDash(state === "rejected" ? [7, 7] : []);
        if (conectaSeleccionado) {
          contextoGrafo.strokeStyle = `rgba(125, 169, 255, ${Math.min(1, depthOpacity + 0.25)})`;
        } else if (structuralColor) {
          contextoGrafo.strokeStyle = structuralColor;
        } else if (state === "selected") {
          contextoGrafo.strokeStyle = `rgba(115, 240, 207, ${depthOpacity})`;
        } else if (state === "rejected") {
          contextoGrafo.strokeStyle = `rgba(255, 130, 155, ${depthOpacity})`;
        } else {
          contextoGrafo.strokeStyle = `rgba(139, 159, 191, ${depthOpacity * 0.62})`;
        }
        contextoGrafo.lineWidth = conectaSeleccionado || structuralColor
          ? 3.4 : state === "selected" ? 3.4 : 1.65;
        contextoGrafo.shadowColor = conectaSeleccionado
          ? "rgba(125, 169, 255, .8)"
          : item.isBottleneck
            ? "rgba(185, 170, 255, .78)"
            : item.isBridge
              ? "rgba(255, 200, 120, .72)"
              : state === "selected" ? "rgba(91, 246, 209, .8)" : "transparent";
        contextoGrafo.shadowBlur = conectaSeleccionado || structuralColor
          ? 13 : state === "selected" ? 13 : 0;
        contextoGrafo.stroke();
        contextoGrafo.setLineDash([]);
        contextoGrafo.shadowBlur = 0;

        const deltaX = item.to.x - item.from.x;
        const deltaY = item.to.y - item.from.y;
        const length = Math.hypot(deltaX, deltaY) || 1;
        const labelOffset = item.index % 2 === 0 ? 11 : -11;
        const midX = (item.from.x + item.to.x) / 2 - (deltaY / length) * labelOffset;
        const midY = (item.from.y + item.to.y) / 2 + (deltaX / length) * labelOffset;
        const label = String(item.edge.peso);
        contextoGrafo.font = "700 11px Inter, system-ui, sans-serif";
        const pillWidth = Math.max(29, contextoGrafo.measureText(label).width + 13);
        if (item.isBottleneck) {
          contextoGrafo.fillStyle = "rgba(58, 48, 91, .96)";
        } else if (item.isBridge) {
          contextoGrafo.fillStyle = "rgba(76, 57, 34, .96)";
        } else if (state === "selected") {
          contextoGrafo.fillStyle = "rgba(19, 62, 59, .94)";
        } else if (state === "rejected") {
          contextoGrafo.fillStyle = "rgba(73, 37, 55, .94)";
        } else {
          contextoGrafo.fillStyle = "rgba(30, 44, 66, .92)";
        }
        contextoGrafo.strokeStyle = state === "selected"
          ? "rgba(115, 240, 207, .62)"
          : item.isBottleneck
            ? "rgba(185, 170, 255, .72)"
            : item.isBridge
              ? "rgba(255, 200, 120, .65)"
              : state === "rejected" ? "rgba(255, 130, 155, .48)" : "rgba(173, 194, 224, .2)";
        contextoGrafo.lineWidth = 1;
        contextoGrafo.beginPath();
        contextoGrafo.roundRect(midX - pillWidth / 2, midY - 10, pillWidth, 20, 7);
        contextoGrafo.fill();
        contextoGrafo.stroke();
        contextoGrafo.fillStyle = item.isBottleneck
          ? "#c8bcff"
          : item.isBridge ? "#ffd79c"
            : state === "selected" ? "#8ff5d7" : state === "rejected" ? "#ff9aae" : "#d9e3f2";
        contextoGrafo.textAlign = "center";
        contextoGrafo.textBaseline = "middle";
        contextoGrafo.fillText(label, midX, midY + 0.5);
      }

      const drawVertices = vertices.map((vertex) => ({
        vertex,
        ...posiciones.get(vertex)
      })).sort((a, b) => a.z - b.z);
      for (const node of drawVertices) {
        const nodeRadius = Math.max(11, Math.min(20, 15 * node.scale));
        const opacity = 0.58 + ((node.z + 1) / 2) * 0.42;
        const isSelected = node.vertex === verticeSeleccionado;
        contextoGrafo.globalAlpha = opacity;
        if (isSelected) {
          contextoGrafo.beginPath();
          contextoGrafo.arc(node.x, node.y, nodeRadius + 7, 0, Math.PI * 2);
          contextoGrafo.fillStyle = "rgba(115, 240, 207, .14)";
          contextoGrafo.fill();
          contextoGrafo.strokeStyle = "rgba(115, 240, 207, .9)";
          contextoGrafo.lineWidth = 2;
          contextoGrafo.stroke();
        }
        contextoGrafo.shadowColor = "rgba(3, 10, 23, .6)";
        contextoGrafo.shadowBlur = 18 * node.scale;
        contextoGrafo.shadowOffsetY = 8 * node.scale;
        const gradient = contextoGrafo.createRadialGradient(
          node.x - nodeRadius * 0.35, node.y - nodeRadius * 0.4, 1,
          node.x, node.y, nodeRadius * 1.35
        );
        gradient.addColorStop(0, "#526681");
        gradient.addColorStop(0.52, "#263953");
        gradient.addColorStop(1, "#17263c");
        contextoGrafo.beginPath();
        contextoGrafo.arc(node.x, node.y, nodeRadius, 0, Math.PI * 2);
        contextoGrafo.fillStyle = gradient;
        contextoGrafo.fill();
        contextoGrafo.shadowBlur = 0;
        contextoGrafo.shadowOffsetY = 0;
        contextoGrafo.strokeStyle = `rgba(191, 212, 236, ${0.42 + (node.z + 1) * 0.2})`;
        contextoGrafo.lineWidth = 1.4;
        contextoGrafo.stroke();
        contextoGrafo.fillStyle = "#f3f7ff";
        contextoGrafo.font = `800 ${Math.max(9, Math.min(13, nodeRadius * 0.75))}px Inter, system-ui, sans-serif`;
        contextoGrafo.textAlign = "center";
        contextoGrafo.textBaseline = "middle";
        const label = node.vertex.length > 6 ? `${node.vertex.slice(0, 4)}…` : node.vertex;
        contextoGrafo.fillText(label, node.x, node.y + 0.5);
      }
      contextoGrafo.restore();
    }

    function animarEscena(tiempo) {
      if (ultimoFrame && giroAutomatico && !arrastrando) {
        rotacionY += Math.min(tiempo - ultimoFrame, 50) * 0.00013;
      }
      ultimoFrame = tiempo;
      dibujarEscena3D();
      if (giroAutomatico || arrastrando) {
        frameAnimacion = window.requestAnimationFrame(animarEscena);
      } else {
        frameAnimacion = null;
      }
    }

    function iniciarAnimacion() {
      if (frameAnimacion === null) {
        ultimoFrame = 0;
        frameAnimacion = window.requestAnimationFrame(animarEscena);
      }
    }

    function actualizarControlGiro() {
      const boton = document.getElementById("toggle-rotation");
      boton.textContent = giroAutomatico ? "Ⅱ Pausar giro" : "▶ Activar giro";
      boton.setAttribute("aria-pressed", String(giroAutomatico));
      document.getElementById("graph-view-status").textContent =
        giroAutomatico ? "Vista 3D activa" : "Vista 3D pausada";
    }

    canvasGrafo.addEventListener("pointerdown", (evento) => {
      arrastrando = true;
      posicionPuntero = { x: evento.clientX, y: evento.clientY };
      inicioPuntero = { x: evento.clientX, y: evento.clientY };
      seMovioPuntero = false;
      canvasGrafo.setPointerCapture(evento.pointerId);
      iniciarAnimacion();
    });

    document.getElementById("history-refresh").addEventListener("click", () => {
      void cargarHistorial();
    });
    document.getElementById("logout").addEventListener("click", async () => {
      await fetch("/api/logout", { method: "POST" });
      window.location.assign("/login");
    });

    canvasGrafo.addEventListener("pointermove", (evento) => {
      if (!arrastrando || !posicionPuntero) return;
      const deltaX = evento.clientX - posicionPuntero.x;
      const deltaY = evento.clientY - posicionPuntero.y;
      if (inicioPuntero && Math.hypot(evento.clientX - inicioPuntero.x, evento.clientY - inicioPuntero.y) > 6) {
        seMovioPuntero = true;
      }
      rotacionY += deltaX * 0.008;
      rotacionX = Math.max(-1.25, Math.min(1.25, rotacionX + deltaY * 0.008));
      posicionPuntero = { x: evento.clientX, y: evento.clientY };
      if (!giroAutomatico) dibujarEscena3D();
    });

    function terminarArrastre(evento) {
      if (!arrastrando) return;
      const seleccionar = evento.type === "pointerup" && !seMovioPuntero;
      arrastrando = false;
      posicionPuntero = null;
      inicioPuntero = null;
      if (canvasGrafo.hasPointerCapture(evento.pointerId)) {
        canvasGrafo.releasePointerCapture(evento.pointerId);
      }
      if (seleccionar) {
        const rectangulo = canvasGrafo.getBoundingClientRect();
        seleccionarVerticeCercano(evento.clientX - rectangulo.left, evento.clientY - rectangulo.top);
      }
      if (giroAutomatico) iniciarAnimacion();
      else if (frameAnimacion !== null) {
        window.cancelAnimationFrame(frameAnimacion);
        frameAnimacion = null;
        dibujarEscena3D();
      }
    }

    canvasGrafo.addEventListener("pointerup", terminarArrastre);
    canvasGrafo.addEventListener("pointercancel", terminarArrastre);
    canvasGrafo.addEventListener("keydown", (evento) => {
      if (!["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp"].includes(evento.key) || !vertices.length) return;
      evento.preventDefault();
      const actual = vertices.indexOf(verticeSeleccionado);
      const direccion = evento.key === "ArrowRight" || evento.key === "ArrowDown" ? 1 : -1;
      const siguiente = actual < 0
        ? direccion > 0 ? 0 : vertices.length - 1
        : (actual + direccion + vertices.length) % vertices.length;
      seleccionarVertice(vertices[siguiente]);
    });
    document.getElementById("toggle-rotation").addEventListener("click", () => {
      giroAutomatico = !giroAutomatico;
      actualizarControlGiro();
      if (giroAutomatico) {
        iniciarAnimacion();
      } else if (!arrastrando && frameAnimacion !== null) {
        window.cancelAnimationFrame(frameAnimacion);
        frameAnimacion = null;
        dibujarEscena3D();
      }
    });
    preferenciaMovimientoReducido.addEventListener("change", (evento) => {
      if (evento.matches && giroAutomatico) {
        giroAutomatico = false;
        actualizarControlGiro();
        if (!arrastrando && frameAnimacion !== null) {
          window.cancelAnimationFrame(frameAnimacion);
          frameAnimacion = null;
          dibujarEscena3D();
        }
      }
    });
    new ResizeObserver(dibujarEscena3D).observe(canvasGrafo);
    actualizarControlGiro();

    function dibujarPasos() {
      const pesosRepetidos = new Map();
      aristas.forEach(({ peso }) => pesosRepetidos.set(peso, (pesosRepetidos.get(peso) ?? 0) + 1));
      const gruposEmpatados = [...pesosRepetidos.values()].filter((cantidad) => cantidad > 1).length;
      document.getElementById("tie-count").textContent = gruposEmpatados
        ? `${gruposEmpatados} ${gruposEmpatados === 1 ? "empate" : "empates"} de peso`
        : "Sin empates";
      listaPasos.innerHTML = pasos.map((paso, indice) => {
        const revisado = indice < pasoActual;
        const actual = indice === pasoActual && pasoActual < pasos.length;
        const empate = pesosRepetidos.get(paso.peso) > 1;
        const decision = revisado
          ? `<span class="badge ${paso.agrega ? "added" : "cycle"}">${paso.agrega ? "Se agrega" : "Cierra ciclo"}</span>`
          : `<span class="badge">${paso.peso}</span>`;
        return `<div class="step${actual ? " current" : ""}">
          <span class="step-number">${String(indice + 1).padStart(2, "0")}</span>
          <span><span class="step-edge">${escaparHtml(paso.desde)}–${escaparHtml(paso.hasta)} <span class="step-detail">${revisado ? escaparHtml(paso.detalle) : `Peso ${paso.peso}`}</span></span></span>
          <span>${decision}${empate ? '<span class="badge tie">Empate</span>' : ""}</span>
        </div>`;
      }).join("");

      document.getElementById("progress").textContent = `${pasoActual} de ${pasos.length}`;
      const barraProgreso = document.getElementById("progress-track");
      barraProgreso.setAttribute("aria-valuemax", Math.max(pasos.length, 1));
      barraProgreso.setAttribute("aria-valuenow", pasoActual);
      document.getElementById("progress-fill").style.width =
        `${pasos.length ? (pasoActual / pasos.length) * 100 : 0}%`;
      document.getElementById("previous").disabled = pasoActual === 0;
      document.getElementById("show-all").disabled = pasoActual === pasos.length || pasos.length === 0;
      const aceptadas = pasos.slice(0, pasoActual).filter((paso) => paso.agrega);
      const resultadoKruskal = analisis.kruskal;
      const pasoProcesado = pasoActual > 0 ? pasos[pasoActual - 1] : null;
      const componentesRestantes = pasoProcesado
        ? pasoProcesado.componentes_restantes
        : resultadoKruskal.vertices_count;
      document.getElementById("component-count").textContent =
        `Componentes restantes: ${componentesRestantes}`;
      const procesado = pasoActual === pasos.length;
      const desconectado = procesado && !resultadoKruskal.connected;
      const completo = procesado && resultadoKruskal.connected;
      botonSiguiente.textContent = desconectado
        ? "No se pudo conectar"
        : pasos.length === 0 || pasoActual === pasos.length
          ? "Árbol completo"
          : pasoActual === 0 ? "Ver primer paso" : "Ver siguiente paso";
      botonSiguiente.disabled = pasos.length === 0 || pasoActual === pasos.length;

      document.getElementById("selected-edges").innerHTML = aceptadas.length
        ? aceptadas.map((paso) => `<span class="chip">${escaparHtml(paso.desde)}–${escaparHtml(paso.hasta)} · peso ${paso.peso}</span>`).join("")
        : '<span class="status">Avanza para construir el árbol</span>';

      const explicacion = document.getElementById("step-explanation-text");
      if (completo) {
        const conexiones = aceptadas.map((paso) => `${paso.desde}–${paso.hasta}`).join(", ");
        explicacion.textContent = resultadoKruskal.stats.edges_selected
          ? `Árbol terminado: se agregaron ${conexiones}. Con ${resultadoKruskal.stats.edges_selected} aristas se conectan los ${resultadoKruskal.vertices_count} vértices sin ciclos; el peso mínimo total es ${resultadoKruskal.total_weight}.`
          : `El grafo tiene un solo vértice, por lo que ya está conectado y no necesita aristas. Su árbol mínimo tiene peso 0.`;
      } else if (desconectado) {
        explicacion.textContent = `Se revisaron todas las aristas, pero quedan ${componentesRestantes} componentes desconectadas. No existe un árbol que conecte todos los vértices; las aristas aceptadas forman el bosque mínimo.`;
      } else if (pasoActual === 0) {
        explicacion.textContent = pasos.length
          ? `Kruskal ordena las aristas de menor a mayor peso. La primera que evaluará es ${pasos[0].desde}–${pasos[0].hasta} (peso ${pasos[0].peso}); se agrega solo si conecta componentes distintas.`
          : `Este grafo no tiene aristas y contiene ${vertices.length} componentes aisladas. No es posible conectarlas para formar un árbol.`;
      } else {
        const paso = pasos[pasoActual - 1];
        const componentes = paso.componentes_restantes;
        explicacion.textContent = paso.agrega
          ? `Paso ${pasoActual}: se agrega ${paso.desde}–${paso.hasta} (peso ${paso.peso}) porque sus extremos estaban en componentes distintas. Así se conectan sin crear un ciclo; quedan ${componentes} ${componentes === 1 ? "componente" : "componentes"}.`
          : `Paso ${pasoActual}: se descarta ${paso.desde}–${paso.hasta} (peso ${paso.peso}) porque sus extremos ya estaban conectados por un camino. Agregarla cerraría un ciclo; el árbol no cambia y quedan ${componentes} ${componentes === 1 ? "componente" : "componentes"}.`;
      }

      document.querySelector(".total-label").textContent = desconectado
        ? "Peso total del bosque encontrado"
        : "Peso total del árbol";
      document.getElementById("total").textContent = procesado
        ? resultadoKruskal.total_weight
        : pasoProcesado ? pasoProcesado.peso_acumulado : "—";
      document.getElementById("result-status").textContent = completo
        ? "Conectado · sin ciclos"
        : desconectado ? "Grafo desconectado" : "En construcción";
      document.getElementById("check").innerHTML = completo
        ? `Comprobación: <strong>${resultadoKruskal.vertices_count} vértices, ${resultadoKruskal.stats.edges_selected} aristas y conexo</strong>. El resultado es un árbol.`
        : desconectado
          ? `No hay aristas suficientes para conectar todos los vértices. Kruskal encontró un bosque de ${resultadoKruskal.stats.edges_selected} ${resultadoKruskal.stats.edges_selected === 1 ? "arista" : "aristas"}.`
          : `Se necesitan <strong>n − 1 = ${resultadoKruskal.edges_required} aristas</strong> para conectar los ${resultadoKruskal.vertices_count} vértices sin ciclos.`;
      actualizarExplicacionVertice();
      dibujarEscena3D();
      dibujarComparacion();
    }

    function dibujarComparacion() {
      if (!analisis) return;
      const resultadoKruskal = analisis.kruskal;
      const resultadoPrim = analisis.prim;
      const estadisticas = resultadoKruskal.stats;
      document.getElementById("stat-examined").textContent = estadisticas.edges_examined;
      document.getElementById("stat-selected").textContent = estadisticas.edges_selected;
      document.getElementById("stat-rejected").textContent = estadisticas.edges_rejected;
      document.getElementById("stat-complexity").textContent = estadisticas.complexity;
      document.getElementById("prim-status").textContent = resultadoPrim.connected
        ? "Árbol generador mínimo"
        : `Bosque mínimo · ${resultadoPrim.components} componentes`;
      document.getElementById("prim-total").textContent = resultadoPrim.total_weight;
      document.getElementById("prim-edges").innerHTML = resultadoPrim.edges.length
        ? resultadoPrim.edges.map((edge) =>
          `<span class="chip">${escaparHtml(edge.desde)}–${escaparHtml(edge.hasta)} · peso ${edge.peso}</span>`
        ).join("")
        : '<span class="status">No se necesitan aristas</span>';
      const mensaje = document.getElementById("comparison-status");
      mensaje.textContent = analisis.pesos_iguales
        ? "Coincidencia: Kruskal y Prim encuentran el mismo peso mínimo."
        : "Atención: los algoritmos produjeron pesos distintos.";
      mensaje.classList.toggle("match", analisis.pesos_iguales);
      dibujarAnalisisEstructural();
    }

    async function cargarHistorial() {
      const lista = document.getElementById("history-list");
      const mensaje = document.getElementById("history-message");
      try {
        const respuesta = await fetch("/api/history", { cache: "no-store" });
        if (respuesta.status === 401) {
          window.location.assign("/login");
          return;
        }
        const resultado = await respuesta.json();
        if (!respuesta.ok) throw new Error(resultado.error || "No se pudo cargar el historial.");
        lista.replaceChildren();
        resultado.history.forEach((record) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "history-item";
          const heading = document.createElement("strong");
          heading.textContent = `Análisis #${record.id} · ${record.analysis.kruskal.total_weight} de peso`;
          const details = document.createElement("span");
          details.textContent = `${record.vertices.join(", ")} · ${record.vertices.length} vértices · ${new Date(record.created_at).toLocaleString()}`;
          button.append(heading, details);
          button.addEventListener("click", () => abrirAnalisisGuardado(record));
          lista.append(button);
        });
        mensaje.textContent = resultado.history.length
          ? `${resultado.history.length} análisis recientes. Selecciona uno para volver a verlo.`
          : "Todavía no hay análisis guardados. Calcula un grafo para agregarlo al historial.";
      } catch (error) {
        if (error instanceof TypeError) {
          mensaje.textContent = "No se pudo contactar al servidor para cargar el historial.";
        } else {
          mensaje.textContent = error.message;
        }
      }
    }

    function abrirAnalisisGuardado(record) {
      vertices = [...record.vertices];
      aristas = record.edges.map(([desde, hasta, peso], indice) => ({
        desde, hasta, peso, indice
      }));
      analisis = record.analysis;
      pasos = analisis.kruskal.steps;
      pasoActual = pasos.length;
      verticeSeleccionado = null;
      document.getElementById("vertices-input").value = vertices.join(", ");
      document.getElementById("edges-input").value = aristas
        .map(({ desde, hasta, peso }) => `${desde}, ${hasta}, ${peso}`).join("\n");
      dibujarGrafo();
      dibujarPasos();
      const aviso = document.getElementById("editor-message");
      aviso.classList.remove("error");
      aviso.textContent = `Se abrió el análisis guardado #${record.id}.`;
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    async function actualizarSesion() {
      try {
        const response = await fetch("/api/session", { cache: "no-store" });
        const session = await response.json();
        document.getElementById("logout").hidden = !session.authentication_required;
      } catch (error) {
        document.getElementById("history-message").textContent =
          error instanceof TypeError ? "No se pudo verificar la sesión." : error.message;
      }
    }

    function dibujarAnalisisEstructural() {
      if (!analisis) return;
      const cuello = document.getElementById("bottleneck-edges");
      cuello.innerHTML = analisis.cuello_botella.length
        ? analisis.cuello_botella.map((edge) =>
          `<span class="chip bottleneck-chip">${escaparHtml(edge.desde)}–${escaparHtml(edge.hasta)} · peso ${edge.peso}</span>`
        ).join("")
        : '<span class="status">No hay aristas en el árbol mínimo</span>';
      const puentes = document.getElementById("bridge-edges");
      puentes.innerHTML = analisis.cortaduras.puentes.length
        ? analisis.cortaduras.puentes.map((edge) =>
          `<span class="chip bridge-chip">${escaparHtml(edge.desde)}–${escaparHtml(edge.hasta)} · peso ${edge.peso}</span>`
        ).join("")
        : '<span class="status">No se encontraron puentes</span>';
      const articulaciones = document.getElementById("articulation-vertices");
      articulaciones.innerHTML = analisis.cortaduras.vertices_articulacion.length
        ? analisis.cortaduras.vertices_articulacion.map((vertex) =>
          `<span class="chip articulation-chip">${escaparHtml(vertex)}</span>`
        ).join("")
        : '<span class="status">No se encontraron vértices de articulación</span>';
    }

    async function cargarGrafo(nuevosVertices, nuevasAristas, mensaje, guardar = true) {
      const aviso = document.getElementById("editor-message");
      aviso.classList.remove("error");
      aviso.textContent = "Calculando el grafo con el núcleo Python…";
      try {
        const respuesta = await fetch("/api/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            vertices: nuevosVertices,
            save: guardar,
            edges: nuevasAristas.map((arista) =>
              arista.campos ?? [arista.desde, arista.hasta, String(arista.peso)]
            )
          })
        });
        const resultado = await respuesta.json();
        if (respuesta.status === 401) {
          window.location.assign("/login");
          return;
        }
        if (!respuesta.ok) throw new Error(resultado.error || "No fue posible calcular el grafo.");
        vertices = [...nuevosVertices];
        aristas = nuevasAristas.map((arista, indice) => ({ ...arista, indice }));
        analisis = resultado;
        pasos = resultado.kruskal.steps;
        pasoActual = 0;
        verticeSeleccionado = null;
        dibujarGrafo();
        dibujarPasos();
        if (guardar) void cargarHistorial();
        aviso.classList.remove("error");
        aviso.textContent = mensaje;
      } catch (error) {
        aviso.classList.add("error");
        aviso.textContent = error instanceof TypeError
          ? "No se pudo contactar al servidor local. Inícialo con «py -m kruskal_app.adapters.web»."
          : error.message;
      }
    }

    document.getElementById("graph-form").addEventListener("submit", (evento) => {
      evento.preventDefault();
      const aviso = document.getElementById("editor-message");
      const nuevosVertices = document.getElementById("vertices-input").value
        .split(",").map((vertice) => vertice.trim()).filter(Boolean);
      const nuevasAristas = document.getElementById("edges-input").value.split(/\r?\n/)
        .map((linea) => linea.trim())
        .filter(Boolean)
        .map((linea) => {
          const campos = linea.split(",").map((campo) => campo.trim());
          return {
            desde: campos[0] ?? "",
            hasta: campos[1] ?? "",
            peso: campos[2] ?? "",
            campos
          };
        });
      void cargarGrafo(nuevosVertices, nuevasAristas, "Grafo actualizado. Avanza para ver cada decisión.");
    });

    document.getElementById("example").addEventListener("click", () => {
      document.getElementById("vertices-input").value = ejemploVertices.join(", ");
      document.getElementById("edges-input").value = ejemploAristas
        .map(({ desde, hasta, peso }) => `${desde}, ${hasta}, ${peso}`).join("\n");
      void cargarGrafo(ejemploVertices, ejemploAristas, "Se cargó el ejemplo original.");
    });

    botonSiguiente.addEventListener("click", () => {
      if (pasoActual < pasos.length) {
        pasoActual += 1;
        dibujarPasos();
      }
    });

    document.getElementById("previous").addEventListener("click", () => {
      if (pasoActual > 0) {
        pasoActual -= 1;
        dibujarPasos();
      }
    });

    document.getElementById("show-all").addEventListener("click", () => {
      pasoActual = pasos.length;
      dibujarPasos();
    });

    document.getElementById("reset").addEventListener("click", () => {
      pasoActual = 0;
      dibujarPasos();
    });

    document.getElementById("vertices-input").value = vertices.join(", ");
    document.getElementById("edges-input").value = aristas
      .map(({ desde, hasta, peso }) => `${desde}, ${hasta}, ${peso}`).join("\n");
    iniciarAnimacion();
    void cargarGrafo(vertices, aristas, "Grafo listo. Avanza para ver cada decisión.", false);
    void cargarHistorial();
    void actualizarSesion();
