-- Minimal internal WhatsApp visit follow-up config for Vertice360 demo

create table if not exists visit_followup_config (
    cliente text primary key,
    enabled boolean not null default true,
    advisor_phone text,
    supervisor_phone text,
    first_delay_seconds integer not null,
    second_delay_seconds integer not null,
    level1_template text,
    level2_template text,
    board_base_url text,
    allow_manual_evaluate boolean not null default true,
    updated_at timestamptz not null default now(),
    updated_by text,
    constraint chk_visit_followup_config_first_delay_positive
        check (first_delay_seconds > 0),
    constraint chk_visit_followup_config_second_delay_positive
        check (second_delay_seconds > 0)
);

alter table visit_followup_config add column if not exists cliente text;
alter table visit_followup_config add column if not exists enabled boolean;
alter table visit_followup_config add column if not exists advisor_phone text;
alter table visit_followup_config add column if not exists supervisor_phone text;
alter table visit_followup_config add column if not exists first_delay_seconds integer;
alter table visit_followup_config add column if not exists second_delay_seconds integer;
alter table visit_followup_config add column if not exists level1_template text;
alter table visit_followup_config add column if not exists level2_template text;
alter table visit_followup_config add column if not exists board_base_url text;
alter table visit_followup_config add column if not exists allow_manual_evaluate boolean;
alter table visit_followup_config add column if not exists updated_at timestamptz;
alter table visit_followup_config add column if not exists updated_by text;
alter table visit_followup_config alter column enabled set default true;
alter table visit_followup_config alter column allow_manual_evaluate set default true;
alter table visit_followup_config alter column updated_at set default now();

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'chk_visit_followup_config_first_delay_positive'
    ) then
        alter table visit_followup_config
        add constraint chk_visit_followup_config_first_delay_positive
        check (first_delay_seconds > 0);
    end if;

    if not exists (
        select 1
        from pg_constraint
        where conname = 'chk_visit_followup_config_second_delay_positive'
    ) then
        alter table visit_followup_config
        add constraint chk_visit_followup_config_second_delay_positive
        check (second_delay_seconds > 0);
    end if;
end
$$;
