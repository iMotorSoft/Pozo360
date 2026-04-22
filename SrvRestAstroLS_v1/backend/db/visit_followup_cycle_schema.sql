-- Minimal internal WhatsApp visit follow-up runtime state for Vertice360 demo

create table if not exists visit_followup_cycle (
    cycle_id text primary key,
    ticket_id text not null,
    cliente text not null,
    status text not null,
    started_at timestamptz not null,
    last_human_action_at timestamptz,
    level1_sent_at timestamptz,
    level2_sent_at timestamptz,
    cancel_reason text,
    closed_at timestamptz,
    project_code text,
    lead_phone text,
    advisor_phone text,
    supervisor_phone text,
    last_evaluated_at timestamptz,
    last_stage_seen text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint chk_visit_followup_cycle_status_not_blank
        check (length(trim(status)) > 0)
);

alter table visit_followup_cycle add column if not exists cycle_id text;
alter table visit_followup_cycle add column if not exists ticket_id text;
alter table visit_followup_cycle add column if not exists cliente text;
alter table visit_followup_cycle add column if not exists status text;
alter table visit_followup_cycle add column if not exists started_at timestamptz;
alter table visit_followup_cycle add column if not exists last_human_action_at timestamptz;
alter table visit_followup_cycle add column if not exists level1_sent_at timestamptz;
alter table visit_followup_cycle add column if not exists level2_sent_at timestamptz;
alter table visit_followup_cycle add column if not exists cancel_reason text;
alter table visit_followup_cycle add column if not exists closed_at timestamptz;
alter table visit_followup_cycle add column if not exists project_code text;
alter table visit_followup_cycle add column if not exists lead_phone text;
alter table visit_followup_cycle add column if not exists advisor_phone text;
alter table visit_followup_cycle add column if not exists supervisor_phone text;
alter table visit_followup_cycle add column if not exists last_evaluated_at timestamptz;
alter table visit_followup_cycle add column if not exists last_stage_seen text;
alter table visit_followup_cycle add column if not exists created_at timestamptz;
alter table visit_followup_cycle add column if not exists updated_at timestamptz;
alter table visit_followup_cycle alter column created_at set default now();
alter table visit_followup_cycle alter column updated_at set default now();

create index if not exists idx_visit_followup_cycle_ticket_id
    on visit_followup_cycle (ticket_id);

create index if not exists idx_visit_followup_cycle_status
    on visit_followup_cycle (status);

create index if not exists idx_visit_followup_cycle_cliente_status
    on visit_followup_cycle (cliente, status);

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'chk_visit_followup_cycle_status_not_blank'
    ) then
        alter table visit_followup_cycle
        add constraint chk_visit_followup_cycle_status_not_blank
        check (length(trim(status)) > 0);
    end if;
end
$$;
