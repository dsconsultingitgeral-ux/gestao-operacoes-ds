# Documentação Técnica e Queries - Gestão e Operações DS

Estrutura das tabelas da base de dados partilhada no Supabase para a plataforma de Gestão e Operações.

## 1. Tabela de Picagens de Ponto
```sql
CREATE TABLE IF NOT EXISTS picagens (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL,
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    hora_entrada TIME,
    hora_saida_almoco TIME,
    hora_entrada_almoco TIME,
    hora_saida TIME,
    horas_totais NUMERIC(4,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projetos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome_projeto TEXT NOT NULL,
    cliente TEXT NOT NULL,
    horas_estimadas NUMERIC(6,2) DEFAULT 0.00,
    estado TEXT NOT NULL DEFAULT 'Ativo' CHECK (estado IN ('Ativo', 'Concluído', 'Pausado')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS projetos_horas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    projeto_id BIGINT REFERENCES projetos(id),
    username TEXT NOT NULL,
    data DATE NOT NULL DEFAULT CURRENT_DATE,
    horas_dedicadas NUMERIC(4,2) NOT NULL,
    descricao TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ferias (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('Férias', 'Doença', 'Formação', 'Outros')),
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    dias_uteis INT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'Pendente' CHECK (estado IN ('Pendente', 'Aprovado', 'Rejeitado')),
    observacoes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
