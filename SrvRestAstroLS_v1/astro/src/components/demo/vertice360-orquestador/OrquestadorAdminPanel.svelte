<script>
  import { onMount } from "svelte";
  import {
    followupConfigGet,
    followupConfigSet,
    followupEvaluate,
    resetRuntimeAll,
    resetRuntimePhone,
  } from "../../../lib/vertice360_orquestador/api.js";

  let { initialCliente = "", initialPhone = "" } = $props();

  const TOKEN_STORAGE_KEY = "VERTICE360_ORQ_ADMIN_TOKEN_SESSION";
  const DEFAULT_CLIENTE = "prod-celulares-check-20260324";
  const DEFAULT_UPDATED_BY = "demo-admin-page";
  const DEFAULT_CONFIRM = "RESET_RUNTIME_ONLY";

  let adminToken = $state("");
  let cliente = $state(String(initialCliente || "").trim() || DEFAULT_CLIENTE);
  let resetPhone = $state("");
  let ticketId = $state("");
  let updatedBy = $state(DEFAULT_UPDATED_BY);

  let enabled = $state(true);
  let advisorPhone = $state("");
  let supervisorPhone = $state("");
  let firstDelaySeconds = $state("10");
  let secondDelaySeconds = $state("15");
  let allowManualEvaluate = $state(true);

  let busyAction = $state("");
  let notice = $state("");
  let errorMessage = $state("");
  let lastAction = $state("");
  let lastResult = $state(null);

  const normalizePhone = (value) => {
    const digits = String(value || "").replace(/\D+/g, "");
    return digits ? `+${digits}` : "";
  };

  const buildDemoLiveUrl = (phoneValue) => {
    const cleanPhone = normalizePhone(phoneValue).replace(/^\+/, "");
    if (!cleanPhone) return "/demo/vertice360-orquestador/";
    return `/demo/vertice360-orquestador/?cliente=${encodeURIComponent(cleanPhone)}`;
  };

  const setResult = (action, payload, successMessage) => {
    lastAction = action;
    lastResult = payload;
    notice = successMessage;
    errorMessage = "";
  };

  const ensureToken = () => {
    const clean = String(adminToken || "").trim();
    if (!clean) {
      throw new Error("Pegá el token admin antes de ejecutar acciones.");
    }
    return clean;
  };

  const persistToken = () => {
    if (typeof window === "undefined") return;
    const clean = String(adminToken || "").trim();
    if (clean) {
      window.sessionStorage.setItem(TOKEN_STORAGE_KEY, clean);
    } else {
      window.sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  };

  const applyConfig = (payload) => {
    enabled = Boolean(payload?.enabled);
    advisorPhone = String(payload?.advisor_phone || "").trim();
    supervisorPhone = String(payload?.supervisor_phone || "").trim();
    firstDelaySeconds = String(payload?.first_delay_seconds ?? "10");
    secondDelaySeconds = String(payload?.second_delay_seconds ?? "15");
    allowManualEvaluate = Boolean(payload?.allow_manual_evaluate);
    updatedBy = String(payload?.updated_by || DEFAULT_UPDATED_BY).trim() || DEFAULT_UPDATED_BY;
  };

  const summarizeEvaluateAction = (action) => {
    const verb = String(action?.action || "").trim();
    const ticket = String(action?.ticket_id || "").trim();
    const statusAfter = String(action?.status_after || "").trim();
    const targetPhone = String(action?.target_phone || "").trim();

    if (verb === "sent_level1" || verb === "sent_level2") {
      const targetSuffix = targetPhone ? ` a ${targetPhone}` : "";
      return `${verb}${targetSuffix}${ticket ? ` (${ticket})` : ""}`;
    }

    if (verb === "no_action") {
      const statusSuffix = statusAfter ? ` en estado ${statusAfter}` : "";
      return `sin acción${statusSuffix}${ticket ? ` (${ticket})` : ""}`;
    }

    if (verb.startsWith("closed_")) {
      return `${verb}${ticket ? ` (${ticket})` : ""}`;
    }

    if (verb === "created_cycle") {
      return `ciclo creado${ticket ? ` (${ticket})` : ""}`;
    }

    return verb || "sin detalle";
  };

  const summarizeEvaluateResult = (payload, fallbackLabel) => {
    const evaluatedCount = Number(payload?.evaluated_count || 0);
    const actions = Array.isArray(payload?.actions) ? payload.actions : [];

    if (evaluatedCount <= 0 || actions.length === 0) {
      return `${fallbackLabel}: sin candidatos para evaluar.`;
    }

    const summary = actions.slice(0, 3).map(summarizeEvaluateAction).join(" | ");
    return `${fallbackLabel}: ${summary}`;
  };

  const runAction = async (action, runner, successMessage) => {
    busyAction = action;
    notice = "";
    errorMessage = "";
    try {
      const payload = await runner();
      const resolvedSuccessMessage =
        typeof successMessage === "function"
          ? successMessage(payload)
          : successMessage;
      setResult(action, payload, resolvedSuccessMessage);
      return payload;
    } catch (err) {
      lastAction = action;
      lastResult = null;
      errorMessage = err?.message || "No se pudo completar la operación.";
      throw err;
    } finally {
      busyAction = "";
    }
  };

  const handleTokenBlur = () => {
    persistToken();
  };

  const loadConfig = async () =>
    runAction(
      "get-config",
      async () => {
        const payload = await followupConfigGet({
          cliente: String(cliente || "").trim(),
          adminToken: ensureToken(),
        });
        applyConfig(payload);
        return payload;
      },
      "Configuración cargada.",
    );

  const saveConfig = async () =>
    runAction(
      "set-config",
      async () =>
        followupConfigSet(
          {
            cliente: String(cliente || "").trim(),
            enabled: Boolean(enabled),
            advisor_phone: normalizePhone(advisorPhone),
            supervisor_phone: normalizePhone(supervisorPhone),
            first_delay_seconds: Number(firstDelaySeconds),
            second_delay_seconds: Number(secondDelaySeconds),
            updated_by: String(updatedBy || DEFAULT_UPDATED_BY).trim() || DEFAULT_UPDATED_BY,
            allow_manual_evaluate: Boolean(allowManualEvaluate),
          },
          { adminToken: ensureToken() },
        ),
      "Configuración guardada.",
    );

  const evaluateGeneral = async () =>
    runAction(
      "evaluate-general",
      async () =>
        followupEvaluate(
          {
            cliente: String(cliente || "").trim(),
            force_now: false,
          },
          { adminToken: ensureToken() },
        ),
      (payload) => summarizeEvaluateResult(payload, "Evaluate general"),
    );

  const evaluateTicket = async () =>
    runAction(
      "evaluate-ticket",
      async () => {
        const cleanTicketId = String(ticketId || "").trim();
        if (!cleanTicketId) throw new Error("Ingresá un ticket_id para evaluate puntual.");
        return followupEvaluate(
          {
            cliente: String(cliente || "").trim(),
            ticket_id: cleanTicketId,
            force_now: false,
          },
          { adminToken: ensureToken() },
        );
      },
      (payload) => summarizeEvaluateResult(payload, "Evaluate por ticket"),
    );

  const runResetPhone = async () =>
    runAction(
      "reset-phone",
      async () => {
        const cleanPhone = normalizePhone(resetPhone);
        if (!cleanPhone) throw new Error("Ingresá un teléfono válido para reset runtime.");
        resetPhone = cleanPhone;
        return resetRuntimePhone(
          { phone: cleanPhone },
          { adminToken: ensureToken() },
        );
      },
      (payload) => {
        const deletedTotal =
          Number(payload?.deleted_total ?? NaN) ||
          Object.values(payload?.deleted || {}).reduce(
            (total, value) => total + Number(value || 0),
            0,
          );
        if (deletedTotal <= 0) {
          return "No se encontró runtime para ese teléfono. Verificá que sea el lead phone real, no advisor/supervisor.";
        }
        return `Runtime por teléfono limpiado (${deletedTotal} registros).`;
      },
    );

  const runResetAll = async () => {
    if (typeof window !== "undefined") {
      const confirmed = window.confirm(
        "Esto borra todo el runtime conversacional de la demo. No toca followup_config ni datos base. ¿Continuar?",
      );
      if (!confirmed) return;
    }
    return runAction(
      "reset-all",
      async () =>
        resetRuntimeAll(
          { confirm: DEFAULT_CONFIRM },
          { adminToken: ensureToken() },
        ),
      "Runtime global limpiado.",
    );
  };

  onMount(() => {
    if (typeof window === "undefined") return;
    adminToken = window.sessionStorage.getItem(TOKEN_STORAGE_KEY) || "";

    const params = new URLSearchParams(window.location.search);
    const queryCliente = String(params.get("cliente") || "").trim();
    const queryPhone = String(params.get("phone") || "").trim();

    if (queryCliente) {
      cliente = queryCliente;
    } else {
      cliente = String(initialCliente || "").trim() || DEFAULT_CLIENTE;
    }

    resetPhone = normalizePhone(queryPhone || initialPhone);
  });
</script>

<section class="space-y-6">
  <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div class="space-y-2">
        <p class="text-xs font-semibold uppercase tracking-[0.22em] text-teal-700">Backstage Operativo</p>
        <h1 class="text-3xl font-semibold tracking-tight text-slate-900">Admin Demo Orquestador</h1>
        <p class="max-w-3xl text-sm text-slate-600">
          Panel operativo para demo presencial. Usa endpoints administrativos reales del orquestador y trabaja
          sobre un <code>cliente</code> lógico y un teléfono lead para limpieza puntual.
        </p>
      </div>
      <div class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        <p class="font-semibold">Uso recomendado</p>
        <p><code>submitted</code> significa ACK aceptado por Gupshup. No equivale a entrega final al teléfono.</p>
      </div>
    </div>
  </div>

  {#if notice}
    <div class="alert border border-emerald-200 bg-emerald-50 text-emerald-900">
      <span>{notice}</span>
    </div>
  {/if}

  {#if errorMessage}
    <div class="alert border border-rose-200 bg-rose-50 text-rose-900">
      <span>{errorMessage}</span>
    </div>
  {/if}

  <div class="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
    <div class="space-y-6">
      <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="mb-5 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Contexto Operativo</h2>
            <p class="text-sm text-slate-500">Token admin, cliente lógico, teléfono lead y ticket puntual.</p>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <label class="form-control gap-2">
            <span class="text-sm font-medium text-slate-700">Token admin</span>
            <input
              class="input input-bordered w-full"
              type="password"
              bind:value={adminToken}
              onblur={handleTokenBlur}
              placeholder="v360-prod-token"
            />
            <span class="text-xs text-slate-500">Se guarda solo en esta pestaña mientras siga abierta.</span>
          </label>

          <label class="form-control gap-2">
            <span class="text-sm font-medium text-slate-700">Cliente lógico</span>
            <input
              class="input input-bordered w-full"
              type="text"
              bind:value={cliente}
              placeholder={DEFAULT_CLIENTE}
            />
            <span class="text-xs text-slate-500">Se usa para config y evaluate.</span>
          </label>

          <label class="form-control gap-2">
            <span class="text-sm font-medium text-slate-700">Teléfono lead para reset</span>
            <input
              class="input input-bordered w-full"
              type="text"
              bind:value={resetPhone}
              placeholder="+59168912007"
            />
            <span class="text-xs text-slate-500">Se usa solo para <code>reset_runtime_phone</code>.</span>
          </label>

          <label class="form-control gap-2">
            <span class="text-sm font-medium text-slate-700">ticket_id opcional</span>
            <input
              class="input input-bordered w-full"
              type="text"
              bind:value={ticketId}
              placeholder="7c8ec3f1-430b-4fb4-8796-382e6b48751c"
            />
            <span class="text-xs text-slate-500">Si queda vacío, evaluate corre en modo general.</span>
          </label>
        </div>

        <div class="mt-5 flex flex-wrap gap-3">
          <a class="btn btn-ghost" href={buildDemoLiveUrl(resetPhone)} target="_blank" rel="noreferrer">
            Abrir Demo Live
          </a>
          <span class="rounded-full border border-slate-200 px-3 py-2 text-xs text-slate-600">
            Demo actual: <code>{normalizePhone(resetPhone) || "sin teléfono"}</code>
          </span>
          <span class="rounded-full border border-slate-200 px-3 py-2 text-xs text-slate-600">
            Evaluate usa cliente: <code>{String(cliente || "").trim() || DEFAULT_CLIENTE}</code>
          </span>
        </div>
      </div>

      <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Follow-up Config</h2>
            <p class="text-sm text-slate-500">Leer y guardar celulares internos y delays del flujo.</p>
          </div>
          <button class="btn btn-outline btn-sm" onclick={loadConfig} disabled={busyAction !== ""}>
            {busyAction === "get-config" ? "Cargando..." : "Get Config"}
          </button>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <label class="form-control gap-2">
            <span class="text-sm font-medium text-slate-700">Advisor phone</span>
            <input class="input input-bordered w-full" type="text" bind:value={advisorPhone} placeholder="+5491130946950" />
          </label>

          <label class="form-control gap-2">
            <span class="text-sm font-medium text-slate-700">Supervisor phone</span>
            <input class="input input-bordered w-full" type="text" bind:value={supervisorPhone} placeholder="+59168912007" />
          </label>

          <label class="form-control gap-2">
            <span class="text-sm font-medium text-slate-700">First delay seconds</span>
            <input class="input input-bordered w-full" type="number" min="1" bind:value={firstDelaySeconds} />
          </label>

          <label class="form-control gap-2">
            <span class="text-sm font-medium text-slate-700">Second delay seconds</span>
            <input class="input input-bordered w-full" type="number" min="1" bind:value={secondDelaySeconds} />
          </label>

          <label class="form-control gap-2">
            <span class="text-sm font-medium text-slate-700">updated_by</span>
            <input class="input input-bordered w-full" type="text" bind:value={updatedBy} />
          </label>

          <div class="grid gap-3 md:grid-cols-2">
            <label class="label cursor-pointer justify-start gap-3 rounded-2xl border border-slate-200 px-4 py-3">
              <input class="checkbox checkbox-sm" type="checkbox" bind:checked={enabled} />
              <span class="label-text text-sm text-slate-700">Enabled</span>
            </label>
            <label class="label cursor-pointer justify-start gap-3 rounded-2xl border border-slate-200 px-4 py-3">
              <input class="checkbox checkbox-sm" type="checkbox" bind:checked={allowManualEvaluate} />
              <span class="label-text text-sm text-slate-700">Allow manual evaluate</span>
            </label>
          </div>
        </div>

        <div class="mt-5 flex flex-wrap gap-3">
          <button class="btn btn-primary" onclick={saveConfig} disabled={busyAction !== ""}>
            {busyAction === "set-config" ? "Guardando..." : "Set Config"}
          </button>
          <button class="btn btn-ghost" onclick={loadConfig} disabled={busyAction !== ""}>
            Recargar config
          </button>
        </div>
      </div>

      <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="mb-5">
          <h2 class="text-lg font-semibold text-slate-900">Acciones Runtime y Follow-up</h2>
          <p class="text-sm text-slate-500">Limpieza puntual del lead y disparo manual de evaluate.</p>
        </div>

        <div class="grid gap-4 lg:grid-cols-2">
          <div class="rounded-2xl border border-slate-200 p-4">
            <div class="mb-3">
              <h3 class="font-semibold text-slate-900">Limpieza Runtime</h3>
              <p class="text-sm text-slate-500">Usa el teléfono lead cargado arriba.</p>
              <p class="mt-1 text-xs text-slate-500">
                Si devuelve todo en cero, ese número no coincide con un lead runtime activo.
              </p>
            </div>
            <div class="flex flex-wrap gap-3">
              <button class="btn btn-secondary" onclick={runResetPhone} disabled={busyAction !== ""}>
                {busyAction === "reset-phone" ? "Limpiando..." : "Reset Runtime Phone"}
              </button>
              <button class="btn btn-outline btn-error" onclick={runResetAll} disabled={busyAction !== ""}>
                {busyAction === "reset-all" ? "Limpiando..." : "Reset Runtime All"}
              </button>
            </div>
          </div>

          <div class="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4">
            <div class="mb-3">
              <h3 class="font-semibold text-slate-900">Evaluate Follow-up</h3>
              <p class="text-sm text-slate-600">
                Dispara el endpoint manual sobre <code>{String(cliente || "").trim() || DEFAULT_CLIENTE}</code>.
              </p>
              <p class="mt-1 text-xs text-slate-500">
                Si cargás <code>ticket_id</code>, el evaluate es puntual. Si no, corre en modo general.
              </p>
            </div>
            <div class="flex flex-wrap gap-3">
              <button class="btn btn-accent" onclick={evaluateGeneral} disabled={busyAction !== ""}>
                {busyAction === "evaluate-general" ? "Evaluando..." : "Evaluate General"}
              </button>
              <button class="btn btn-outline" onclick={evaluateTicket} disabled={busyAction !== ""}>
                {busyAction === "evaluate-ticket" ? "Evaluando..." : "Evaluate por ticket"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <aside class="space-y-6">
      <div class="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-slate-100 shadow-sm">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold">Último resultado</h2>
            <p class="text-sm text-slate-400">Respuesta cruda del backend.</p>
          </div>
          {#if lastAction}
            <span class="rounded-full border border-slate-700 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-300">
              {lastAction}
            </span>
          {/if}
        </div>

        <pre class="max-h-[32rem] overflow-auto rounded-2xl bg-slate-900 p-4 text-xs leading-6 text-emerald-200">{lastResult ? JSON.stringify(lastResult, null, 2) : "Todavía no se ejecutó ninguna acción."}</pre>
      </div>

      <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-slate-900">Notas Operativas</h2>
        <ul class="space-y-3 text-sm text-slate-600">
          <li><strong>`cliente`</strong> se usa para follow-up config y evaluate.</li>
          <li><strong>`reset_runtime_phone`</strong> usa el teléfono lead exacto, no el cliente lógico ni el interno advisor/supervisor.</li>
          <li><strong>`target_phone`</strong> es el destino real del follow-up interno.</li>
          <li><strong>`target_matches_lead`</strong> ayuda a detectar cuando el interno coincide con el lead.</li>
          <li><strong>`submitted`</strong> es aceptación del provider, no entrega final al dispositivo.</li>
        </ul>
      </div>
    </aside>
  </div>
</section>
