<script>
  const flow = [
    {
      step: "01",
      title: "Mensaje",
      subtitle: "Entrada multicanal",
      detail: "WhatsApp, webchat, email, formularios o APIs",
      tone: "message",
    },
    {
      step: "02",
      title: "Nivel 1",
      subtitle: "Responsable asignado",
      detail: "El caso se clasifica y queda trazable",
      tone: "level1",
    },
    {
      step: "03",
      title: "SLA",
      subtitle: "Espera controlada",
      detail: "El workflow mide si la accion ocurre",
      tone: "sla",
    },
    {
      step: "04",
      title: "Nivel 2",
      subtitle: "Escalamiento",
      detail: "Si no hay accion, se notifica al siguiente nivel",
      tone: "level2",
    },
    {
      step: "05",
      title: "Supervisor",
      subtitle: "Intervencion humana",
      detail: "Puede entrar en cualquier conversacion",
      tone: "supervisor",
    },
  ];

  const channels = ["WhatsApp", "Webchat", "Email", "Formularios", "APIs"];
  const domains = ["Empresas", "Municipios", "Organismos publicos"];
</script>

<section class="poster" aria-label="Infografia Vertice360 workflow supervisado">
  <div class="brand">
    <img src="/logo_v360.png" alt="" />
    <div>
      <strong>Vertice360</strong>
      <span>Orquestador de workflows conversacionales</span>
    </div>
  </div>

  <div class="headline">
    <p>Infografia conceptual</p>
    <h1>De un mensaje a un workflow supervisado</h1>
    <h2>Seguimiento, SLA, escalamiento automatico e intervencion humana en tiempo real.</h2>
  </div>

  <div class="signal-message">
    <div class="signal-ring"></div>
    <div class="chat-bubble">
      <span>Mensaje entrante</span>
      <strong>"Necesito resolver este caso"</strong>
    </div>
  </div>

  <div class="flow-map">
    <div class="flow-path"></div>
    {#each flow as item, index}
      <article class={`flow-card ${item.tone}`} style={`left: ${index * 363}px;`}>
        <div class="step-mark">{item.step}</div>
        <div class="icon-wrap" aria-hidden="true">
          {#if item.tone === "message"}
            <svg viewBox="0 0 64 64"><path d="M12 18a10 10 0 0 1 10-10h20a10 10 0 0 1 10 10v14a10 10 0 0 1-10 10H31L19 54V42a10 10 0 0 1-7-10V18Z" /></svg>
          {:else if item.tone === "level1"}
            <svg viewBox="0 0 64 64"><circle cx="32" cy="22" r="11" /><path d="M14 54c3-13 12-20 18-20s15 7 18 20" /></svg>
          {:else if item.tone === "sla"}
            <svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="22" /><path d="M32 16v18l12 8" /></svg>
          {:else if item.tone === "level2"}
            <svg viewBox="0 0 64 64"><path d="M32 8 58 54H6L32 8Z" /><path d="M32 24v14M32 46h.1" /></svg>
          {:else}
            <svg viewBox="0 0 64 64"><rect x="10" y="14" width="44" height="32" rx="7" /><path d="M20 54h24M32 46v8M22 27h20M22 35h12" /></svg>
          {/if}
        </div>
        <div class="copy">
          <p>{item.title}</p>
          <strong>{item.subtitle}</strong>
          <span>{item.detail}</span>
        </div>
      </article>
      {#if index < flow.length - 1}
        <div class={`arrow arrow-${index + 1}`} aria-hidden="true"></div>
      {/if}
    {/each}
  </div>

  <div class="escalation-callout">
    <span>Regla clave</span>
    <strong>Si Nivel 1 no actua, Vertice360 escala automaticamente a Nivel 2.</strong>
  </div>

  <div class="supervisor-callout">
    <span>Control humano</span>
    <strong>El supervisor puede intervenir en cualquier conversacion.</strong>
  </div>

  <div class="bottom-grid">
    <div class="band">
      <p>Canales de entrada</p>
      <div>
        {#each channels as channel}
          <span>{channel}</span>
        {/each}
      </div>
    </div>
    <div class="band">
      <p>Aplicable a</p>
      <div>
        {#each domains as domain}
          <span>{domain}</span>
        {/each}
      </div>
    </div>
  </div>
</section>

<style>
  .poster {
    position: relative;
    width: 1920px;
    height: 1080px;
    overflow: hidden;
    background:
      linear-gradient(115deg, rgba(15, 118, 110, 0.08), transparent 34%),
      linear-gradient(20deg, rgba(14, 165, 233, 0.1), transparent 32%),
      #f6faf9;
    color: #0f172a;
  }

  .poster::before {
    content: "";
    position: absolute;
    inset: 95px 120px auto auto;
    width: 480px;
    height: 480px;
    border: 1px solid rgba(15, 118, 110, 0.18);
    border-radius: 50%;
  }

  .poster::after {
    content: "";
    position: absolute;
    right: -190px;
    bottom: -220px;
    width: 650px;
    height: 650px;
    border-radius: 50%;
    background: rgba(15, 118, 110, 0.08);
  }

  .brand {
    position: absolute;
    top: 58px;
    left: 92px;
    display: flex;
    align-items: center;
    gap: 18px;
  }

  .brand img {
    width: 58px;
    height: 58px;
  }

  .brand strong,
  .brand span {
    display: block;
  }

  .brand strong {
    color: #064e3b;
    font-size: 29px;
    line-height: 1;
  }

  .brand span {
    margin-top: 7px;
    color: #475569;
    font-size: 18px;
  }

  .headline {
    position: absolute;
    top: 166px;
    left: 92px;
    width: 940px;
  }

  .headline p {
    margin: 0 0 18px;
    color: #0f766e;
    font-size: 17px;
    font-weight: 900;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .headline h1 {
    margin: 0;
    color: #064e3b;
    font-size: 76px;
    line-height: 0.98;
    letter-spacing: 0;
  }

  .headline h2 {
    width: 810px;
    margin: 26px 0 0;
    color: #334155;
    font-size: 28px;
    font-weight: 600;
    line-height: 1.36;
  }

  .signal-message {
    position: absolute;
    top: 172px;
    right: 112px;
    width: 520px;
    height: 255px;
  }

  .signal-ring {
    position: absolute;
    inset: 0;
    border: 2px dashed rgba(15, 118, 110, 0.38);
    border-radius: 999px;
    transform: rotate(-8deg);
  }

  .chat-bubble {
    position: absolute;
    top: 64px;
    left: 62px;
    width: 372px;
    border-radius: 34px 34px 34px 10px;
    background: #0f766e;
    box-shadow: 0 28px 80px rgba(15, 118, 110, 0.26);
    color: #ffffff;
    padding: 30px 36px;
  }

  .chat-bubble span,
  .chat-bubble strong {
    display: block;
  }

  .chat-bubble span {
    color: #c7f9ee;
    font-size: 18px;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.12em;
  }

  .chat-bubble strong {
    margin-top: 14px;
    font-size: 30px;
    line-height: 1.18;
  }

  .flow-map {
    position: absolute;
    left: 92px;
    right: 92px;
    top: 500px;
    height: 335px;
  }

  .flow-path {
    position: absolute;
    left: 128px;
    right: 128px;
    top: 101px;
    height: 10px;
    border-radius: 999px;
    background: linear-gradient(90deg, #0f766e, #0ea5e9, #f59e0b, #ef4444, #0f172a);
    opacity: 0.24;
  }

  .flow-card {
    position: absolute;
    top: 0;
    width: 274px;
    height: 310px;
    border: 1px solid rgba(15, 23, 42, 0.12);
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.88);
    box-shadow: 0 32px 90px rgba(15, 23, 42, 0.12);
    backdrop-filter: blur(18px);
  }

  .step-mark {
    position: absolute;
    top: 18px;
    left: 20px;
    color: #64748b;
    font-size: 16px;
    font-weight: 900;
    letter-spacing: 0.16em;
  }

  .icon-wrap {
    position: absolute;
    top: 62px;
    left: 50%;
    display: grid;
    place-items: center;
    width: 118px;
    height: 118px;
    border-radius: 50%;
    transform: translateX(-50%);
  }

  .icon-wrap svg {
    width: 64px;
    height: 64px;
    fill: none;
    stroke: currentColor;
    stroke-width: 5;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  .message .icon-wrap {
    background: #dcfce7;
    color: #0f766e;
  }

  .level1 .icon-wrap {
    background: #e0f2fe;
    color: #0369a1;
  }

  .sla .icon-wrap {
    background: #fef3c7;
    color: #b45309;
  }

  .level2 .icon-wrap {
    background: #fee2e2;
    color: #b91c1c;
  }

  .supervisor .icon-wrap {
    background: #e2e8f0;
    color: #0f172a;
  }

  .copy {
    position: absolute;
    left: 24px;
    right: 24px;
    top: 200px;
    text-align: center;
  }

  .copy p,
  .copy strong,
  .copy span {
    display: block;
  }

  .copy p {
    margin: 0;
    color: #0f172a;
    font-size: 26px;
    font-weight: 950;
  }

  .copy strong {
    margin-top: 6px;
    color: #0f766e;
    font-size: 18px;
  }

  .copy span {
    margin-top: 8px;
    color: #475569;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.26;
  }

  .arrow {
    position: absolute;
    top: 91px;
    width: 60px;
    height: 30px;
  }

  .arrow::before,
  .arrow::after {
    content: "";
    position: absolute;
    background: #0f766e;
  }

  .arrow::before {
    top: 13px;
    left: 0;
    width: 48px;
    height: 4px;
    border-radius: 999px;
  }

  .arrow::after {
    top: 7px;
    right: 5px;
    width: 16px;
    height: 16px;
    border-radius: 3px;
    transform: rotate(45deg);
  }

  .arrow-1 {
    left: 292px;
  }

  .arrow-2 {
    left: 655px;
  }

  .arrow-3 {
    left: 1018px;
  }

  .arrow-4 {
    left: 1381px;
  }

  .escalation-callout,
  .supervisor-callout {
    position: absolute;
    top: 820px;
    width: 710px;
    border-radius: 20px;
    padding: 20px 30px;
    box-shadow: 0 20px 70px rgba(15, 23, 42, 0.12);
  }

  .escalation-callout {
    left: 92px;
    background: #fff7ed;
    border: 1px solid #fed7aa;
  }

  .supervisor-callout {
    right: 92px;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
  }

  .escalation-callout span,
  .supervisor-callout span {
    display: block;
    color: #0f766e;
    font-size: 15px;
    font-weight: 950;
    letter-spacing: 0.16em;
    text-transform: uppercase;
  }

  .escalation-callout strong,
  .supervisor-callout strong {
    display: block;
    margin-top: 9px;
    color: #0f172a;
    font-size: 24px;
    line-height: 1.18;
  }

  .bottom-grid {
    position: absolute;
    left: 92px;
    right: 92px;
    bottom: 32px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 26px;
  }

  .band {
    display: flex;
    align-items: center;
    gap: 20px;
    min-height: 72px;
    border-radius: 18px;
    background: #0f172a;
    padding: 0 24px;
    color: #ffffff;
  }

  .band p {
    flex: 0 0 auto;
    margin: 0;
    color: #5eead4;
    font-size: 16px;
    font-weight: 950;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .band div {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .band span {
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    padding: 8px 12px;
    font-size: 15px;
    font-weight: 850;
  }
</style>
