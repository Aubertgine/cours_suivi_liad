-- À coller une seule fois dans Supabase : menu « SQL Editor » > « New query » > Run.
-- Crée les deux tables et l'espace de stockage privé des documents.

create table if not exists public.seances (
  id            text primary key,
  date          date not null,
  debut         text not null,
  fin           text not null,
  tarif_horaire numeric not null,
  notion        text not null default ''
);

create table if not exists public.versements (
  id      text primary key,
  date    date not null,
  montant numeric not null,
  note    text not null default ''
);

-- Sécurité : personne ne peut lire ces tables depuis l'extérieur,
-- seule l'application (avec la clé secrète) y a accès.
alter table public.seances   enable row level security;
alter table public.versements enable row level security;

-- Espace de stockage PRIVÉ pour les documents joints (PDF, images).
insert into storage.buckets (id, name, public)
values ('documents', 'documents', false)
on conflict (id) do nothing;
