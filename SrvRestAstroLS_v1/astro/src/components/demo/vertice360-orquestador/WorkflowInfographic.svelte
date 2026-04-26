<script>
  import { onMount } from "svelte";

  const contexts = [
    {
      id: "empresa",
      label: "Empresa",
      incoming: "Necesito hablar con ventas por una cotizacion pendiente.",
      level1: "Ejecutivo comercial",
      level2: "Supervisor comercial",
      outcome: "Oportunidad seguida hasta cierre",
    },
    {
      id: "municipio",
      label: "Municipio",
      incoming: "Quiero reclamar por luminarias apagadas en mi cuadra.",
      level1: "Mesa de entrada",
      level2: "Coordinacion de area",
      outcome: "Caso derivado con trazabilidad",
    },
    {
      id: "organismo",
      label: "Organismo publico",
      incoming: "Necesito consultar el estado de mi tramite.",
      level1: "Agente de atencion",
      level2: "Responsable operativo",
      outcome: "Expediente atendido y auditado",
    },
  ];

  const steps = [
    {
      title: "Mensaje",
      label: "Entrada multicanal",
      detail: "Un usuario escribe desde WhatsApp, webchat, email, formulario o API.",
      tone: "emerald",
    },
    {
      title: "Nivel 1",
      label: "Asignacion inicial",
      detail: "Vertice360 crea el caso, clasifica la intencion y asigna responsable.",
      tone: "sky",
    },
    {
      title: "SLA",
      label: "Espera controlada",
      detail: "El workflow mide el tiempo y detecta si la accion esperada no ocurre.",
      tone: "amber",
    },
    {
      title: "Nivel 2",
      label: "Escalamiento",
      detail: "Si Nivel 1 no actua, el sistema notifica al siguiente nivel.",
      tone: "rose",
    },
    {
      title: "Supervisor",
      label: "Intervencion humana",
      detail: "Un supervisor puede entrar en cualquier conversacion y destrabar el caso.",
      tone: "slate",
    },
  ];

  const channels = ["WhatsApp", "Webchat", "Email", "Formularios", "APIs"];
  const domains = ["Comercial", "Atencion ciudadana", "Soporte", "Reclamos", "Tramites"];

  let activeContextId = $state("empresa");
  let activeStep = $state(0);
  let paused = $state(false);

  const getContext = () =>
    contexts.find((context) => context.id === activeContextId) ?? contexts[0];

  const getContextIndex = () => {
    const index = contexts.findIndex((context) => context.id === activeContextId);
    return index >= 0 ? index : 0;
  };

  const advanceContext = () => {
    const nextIndex = (getContextIndex() + 1) % contexts.length;
    activeContextId = contexts[nextIndex].id;
    activeStep = 0;
  };

  const selectContext = (id) => {
    activeContextId = id;
    activeStep = 0;
    paused = false;
  };

  const selectStep = (index) => {
    activeStep = index;
    paused = true;
  };

  onMount(() => {
    const intervalId = window.setInterval(() => {
      if (paused) return;

      if (activeStep >= steps.length - 1) {
        advanceContext();
      } else {
        activeStep += 1;
      }
    }, 1600);

    return () => window.clearInterval(intervalId);
  });
</script>

<svelte:head>
  <title>Vertice360 | Infografia interactiva</title>
</svelte:head>

<section class="workflow-shell mx-auto max-w-6xl">
  <div class="hero-grid">
    <div class="hero-copy">
      <p class="eyebrow">Infografia interactiva</p>
      <h1>Un mensaje dispara un workflow supervisado</h1>
      <p class="hero-subtitle">
        Vertice360 convierte conversaciones en casos trazables, con seguimiento,
        escalamiento automatico e intervencion humana en tiempo real.
      </p>
    </div>

    <div class="context-stack">
      <button
        type="button"
        class="play-toggle"
        class:paused
        onclick={() => (paused = !paused)}
        aria-label={paused ? "Reanudar animacion" : "Pausar animacion"}
      >
        <span class="toggle-icon" aria-hidden="true">
          {#if paused}
            Play
          {:else}
            Pausa
          {/if}
        </span>
      </button>

      <div class="context-panel" aria-label="Contexto de ejemplo">
        <p class="panel-kicker">Caso de uso</p>
        <div class="context-switcher">
          {#each contexts as context}
            <button
              type="button"
              class:active={activeContextId === context.id}
              onclick={() => selectContext(context.id)}
            >
              {context.label}
            </button>
          {/each}
        </div>
        <p class="context-outcome">{getContext().outcome}</p>
      </div>
    </div>
  </div>

  <div class="story-stage" aria-label="Flujo de workflow conversacional">
    <div class="conversation-column">
      <div class="phone-frame">
        <div class="phone-topline">
          <span>Canal activo</span>
          <strong>{channels[activeStep % channels.length]}</strong>
        </div>
        <div class="bubble user-bubble">
          {getContext().incoming}
        </div>
        <div class="bubble system-bubble" class:visible={activeStep >= 1}>
          Caso creado y asignado a {getContext().level1}.
        </div>
        <div class="bubble alert-bubble" class:visible={activeStep >= 3}>
          Nivel 1 sin accion. Escalando a {getContext().level2}.
        </div>
        <div class="bubble supervisor-bubble" class:visible={activeStep >= 4}>
          Supervisor interviene y responde sin perder trazabilidad.
        </div>
      </div>
    </div>

    <div class="flow-column">
      <div class="flow-line" aria-hidden="true"></div>
      {#each steps as step, index}
        <button
          type="button"
          class="flow-node tone-{step.tone}"
          class:active={activeStep === index}
          class:done={activeStep > index}
          onclick={() => selectStep(index)}
          aria-label={`Ver paso ${index + 1}: ${step.title}`}
        >
          <span class="node-index">{index + 1}</span>
          <span class="node-copy">
            <strong>{step.title}</strong>
            <small>{step.label}</small>
          </span>
        </button>
      {/each}
    </div>

    <div class="status-column">
      <div class="status-panel">
        <p class="panel-kicker">Estado del workflow</p>
        <h2>{steps[activeStep].label}</h2>
        <p>{steps[activeStep].detail}</p>

        <div class="sla-meter" class:warning={activeStep >= 2}>
          <span>SLA</span>
          <strong>{activeStep < 2 ? "en curso" : activeStep === 2 ? "00:10" : "vencido"}</strong>
        </div>
      </div>

      <div class="intervention-panel">
        <p class="panel-kicker">Control humano</p>
        <strong>{getContext().level2}</strong>
        <span>puede entrar en cualquier conversacion, responder o destrabar el caso.</span>
      </div>
    </div>
  </div>

  <div class="signal-strip">
    <div>
      <p class="strip-title">Canales</p>
      <div class="chip-list">
        {#each channels as channel}
          <span>{channel}</span>
        {/each}
      </div>
    </div>
    <div>
      <p class="strip-title">Aplicable a</p>
      <div class="chip-list">
        {#each domains as domain}
          <span>{domain}</span>
        {/each}
      </div>
    </div>
  </div>

  <div class="closing-line">
    <strong>La demo usa WhatsApp e inmobiliaria.</strong>
    <span>La logica es la misma para corporaciones, municipios y organismos publicos.</span>
  </div>
</section>

<style>
  .workflow-shell {
    color: #172033;
    margin-top: -18px;
  }

  .hero-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
    gap: 24px;
    align-items: end;
    margin-bottom: 24px;
  }

  .hero-copy {
    padding: 18px 0;
  }

  .eyebrow,
  .panel-kicker,
  .strip-title {
    margin: 0 0 8px;
    color: #0f766e;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  h1 {
    margin: 0;
    max-width: 760px;
    color: #064e3b;
    font-size: 3rem;
    line-height: 1.02;
  }

  .hero-subtitle {
    max-width: 680px;
    margin: 16px 0 0;
    color: #475569;
    font-size: 1.08rem;
    line-height: 1.65;
  }

  .context-panel,
  .status-panel,
  .intervention-panel {
    border: 1px solid #dbe6e4;
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
  }

  .context-panel {
    padding: 18px;
  }

  .context-stack {
    display: grid;
    gap: 8px;
    justify-items: start;
  }

  .context-stack .context-panel {
    width: 100%;
  }

  .play-toggle {
    min-height: 30px;
    border: 1px solid #0f766e;
    border-radius: 999px;
    background: #0f766e;
    color: #ffffff;
    padding: 6px 12px;
    font-size: 0.76rem;
    font-weight: 900;
    cursor: pointer;
    transition:
      background 0.2s ease,
      color 0.2s ease,
      transform 0.2s ease;
  }

  .play-toggle.paused {
    background: #ffffff;
    color: #0f766e;
  }

  .play-toggle:hover {
    transform: translateY(-1px);
  }

  .context-switcher {
    display: grid;
    gap: 8px;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .context-switcher button {
    min-height: 42px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    background: #f8fafc;
    color: #334155;
    font-size: 0.84rem;
    font-weight: 800;
    cursor: pointer;
    transition:
      background 0.2s ease,
      border-color 0.2s ease,
      color 0.2s ease;
  }

  .context-switcher button.active,
  .context-switcher button:hover {
    border-color: #0f766e;
    background: #0f766e;
    color: #ffffff;
  }

  .context-outcome {
    min-height: 24px;
    margin: 14px 0 0;
    color: #475569;
    font-weight: 700;
  }

  .story-stage {
    display: grid;
    grid-template-columns: minmax(260px, 0.95fr) minmax(320px, 1.05fr) minmax(260px, 0.8fr);
    gap: 20px;
    align-items: stretch;
    min-height: 470px;
  }

  .conversation-column,
  .flow-column,
  .status-column {
    min-width: 0;
  }

  .phone-frame {
    min-height: 470px;
    border: 1px solid #dbe6e4;
    border-radius: 8px;
    background:
      linear-gradient(#ffffff, #ffffff) padding-box,
      linear-gradient(135deg, #0f766e, #38bdf8, #f59e0b) border-box;
    padding: 18px;
    box-shadow: 0 20px 60px rgba(15, 23, 42, 0.08);
  }

  .phone-topline {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 18px;
    color: #64748b;
    font-size: 0.83rem;
  }

  .phone-topline strong {
    color: #0f766e;
  }

  .bubble {
    width: fit-content;
    max-width: 92%;
    margin-bottom: 14px;
    border-radius: 8px;
    padding: 12px 14px;
    font-weight: 700;
    line-height: 1.45;
    opacity: 0.24;
    transform: translateY(6px);
    transition:
      opacity 0.25s ease,
      transform 0.25s ease;
  }

  .user-bubble {
    margin-left: auto;
    background: #dcfce7;
    color: #14532d;
    opacity: 1;
    transform: none;
  }

  .system-bubble {
    background: #e0f2fe;
    color: #075985;
  }

  .alert-bubble {
    background: #fef3c7;
    color: #92400e;
  }

  .supervisor-bubble {
    background: #ffe4e6;
    color: #9f1239;
  }

  .bubble.visible {
    opacity: 1;
    transform: translateY(0);
  }

  .flow-column {
    position: relative;
    display: grid;
    gap: 12px;
    align-content: center;
    padding: 6px 0;
  }

  .flow-line {
    position: absolute;
    left: 28px;
    top: 54px;
    bottom: 54px;
    width: 3px;
    border-radius: 999px;
    background: #dbe6e4;
  }

  .flow-node {
    position: relative;
    display: grid;
    grid-template-columns: 56px minmax(0, 1fr);
    align-items: center;
    gap: 12px;
    min-height: 78px;
    border: 1px solid #dbe6e4;
    border-radius: 8px;
    background: #ffffff;
    padding: 12px;
    color: #334155;
    text-align: left;
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
    cursor: pointer;
    transition:
      border-color 0.2s ease,
      box-shadow 0.2s ease,
      transform 0.2s ease;
  }

  .flow-node.active {
    border-color: #0f766e;
    box-shadow: 0 20px 50px rgba(15, 118, 110, 0.16);
    transform: translateX(4px);
  }

  .flow-node.done {
    border-color: #99f6e4;
  }

  .node-index {
    display: grid;
    place-items: center;
    width: 44px;
    height: 44px;
    border-radius: 999px;
    background: #f8fafc;
    color: #0f172a;
    font-weight: 900;
  }

  .flow-node.active .node-index {
    background: #0f766e;
    color: #ffffff;
  }

  .node-copy strong,
  .node-copy small {
    display: block;
  }

  .node-copy strong {
    color: #0f172a;
    font-size: 1rem;
  }

  .node-copy small {
    margin-top: 3px;
    color: #64748b;
    font-size: 0.82rem;
    font-weight: 700;
  }

  .status-column {
    display: grid;
    gap: 16px;
    align-content: center;
  }

  .status-panel,
  .intervention-panel {
    padding: 20px;
  }

  .status-panel h2 {
    margin: 0;
    color: #0f172a;
    font-size: 1.35rem;
    line-height: 1.2;
  }

  .status-panel p {
    margin: 12px 0 0;
    color: #475569;
    line-height: 1.55;
  }

  .sla-meter {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-top: 22px;
    border-radius: 8px;
    background: #ecfdf5;
    padding: 12px 14px;
    color: #065f46;
    font-weight: 900;
  }

  .sla-meter.warning {
    background: #fff7ed;
    color: #9a3412;
  }

  .intervention-panel {
    display: grid;
    gap: 8px;
    border-color: #fecdd3;
    background: #fff7f7;
  }

  .intervention-panel strong {
    color: #9f1239;
    font-size: 1.1rem;
  }

  .intervention-panel span {
    color: #475569;
    line-height: 1.45;
  }

  .signal-strip {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 24px;
    border-top: 1px solid #dbe6e4;
    padding-top: 20px;
  }

  .chip-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .chip-list span {
    border: 1px solid #cbd5e1;
    border-radius: 999px;
    background: #ffffff;
    padding: 8px 12px;
    color: #334155;
    font-size: 0.86rem;
    font-weight: 800;
  }

  .closing-line {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 18px;
    border-radius: 8px;
    background: #0f172a;
    padding: 16px 18px;
    color: #e2e8f0;
  }

  .closing-line strong {
    color: #ffffff;
  }

  @media (max-width: 980px) {
    .hero-grid,
    .story-stage,
    .signal-strip {
      grid-template-columns: 1fr;
    }

    h1 {
      font-size: 2.2rem;
    }

    .phone-frame,
    .story-stage {
      min-height: auto;
    }

    .flow-line {
      display: none;
    }
  }

  @media (max-width: 640px) {
    .context-switcher {
      grid-template-columns: 1fr;
    }

    h1 {
      font-size: 1.8rem;
    }

    .hero-subtitle {
      font-size: 0.98rem;
    }

    .flow-node {
      grid-template-columns: 48px minmax(0, 1fr);
    }
  }
</style>
