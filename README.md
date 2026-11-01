# ⚙️ Enterprise Process Automation (RPA), AI Triage & Cloud Sync (Python · APIs · AWS S3)

[![Automation](https://img.shields.io/badge/Automação-RPA%20%26%20Backoffice-0A66C2)](#)
[![Python](https://img.shields.io/badge/Python-3.12%20·%20REST%20APIs%20·%20Boto3-3776AB?logo=python&logoColor=white)](#)
[![AI Triage](https://img.shields.io/badge/IA-Classificação%20de%20Chamados%20%26%20SLA-FF6F00)](#)
[![Cloud](https://img.shields.io/badge/Cloud-AWS%20S3%20Sync-FF9900?logo=amazonwebservices&logoColor=white)](#)

Pipeline completo de **Automação de Processos Corporativos (RPA / Backoffice), Integração de APIs REST, Classificação Inteligente com IA e Sincronização em Nuvem (AWS S3)** desenvolvido em **Python**.

---

## 🎯 Problema Operacional Resolvido

Equipes financeiras (Contas a Pagar / FinOps) e de Operações de TI gastam dezenas de horas semanais conferindo manualmente planilhas de faturas de fornecedores em dólar/real e fazendo triagem manual de chamados de suporte.

Este projeto automatiza o ciclo inteiro em menos de **2 segundos**:

1. **Integração com API Oficial do Banco Central (PTAX USD/BRL):** Consulta a API OData do BACEN (com fallback resiliente offline) para converter faturas internacionais de Cloud e SaaS.
2. **Robô de Conciliação Financeira e Glosa Automática:** Cruza cada fatura recebida contra o valor contratado e hashes de notas fiscais, bloqueando automaticamente cobranças com variação acima de 5% ou notas fiscais duplicadas.
3. **Motor de Triagem de Chamados com IA/NLP:** Analisa a descrição em texto livre de chamados operacionais, classifica a prioridade (`P1` a `P4`), verifica violações de SLA e define a ação recomendada.
4. **Geração de Entregáveis Executivos (`.xlsx` e `.pdf`) e Upload para AWS S3 (`boto3`):** Gera a planilha auditada em Excel, o relatório de governança em PDF e sincroniza o pacote com bucket S3.

---

## 🏗️ Fluxo da Automação

```mermaid
flowchart LR
    subgraph Fontes["1. Fontes & APIs"]
        API["API PTAX BACEN\n(Câmbio USD/BRL)"]
        FAT["Faturas Fornecedores\n(.csv)"]
        INC["Chamados Service Desk\n(.json)"]
    end

    subgraph Motor["2. Robô Python (RPA & IA)"]
        CONC["Motor de Conciliação\nFinanceira & Glosa"]
        NLP["Classificador IA\nde Prioridade & SLA"]
    end

    subgraph Saida["3. Entregáveis & Cloud"]
        XLSX["Planilha Auditada\n(.xlsx)"]
        PDF["Relatório Executivo\n(.pdf)"]
        S3["AWS S3 Sync\n(boto3)"]
    end

    API & FAT --> CONC --> XLSX & PDF
    INC --> NLP --> PDF
    XLSX & PDF --> S3
```

---

## 📊 Resultados Auditados na Execução Padrão (`seed 42`)

| Indicador Operacional | Resultado |
|---|---|
| **Faturas Processadas pelo Robô** | **60 faturas** (Contratos em BRL e USD convertidos via PTAX) |
| **Faturas Bloqueadas por Divergência / Duplicidade** | **16 faturas** retidas automaticamente para auditoria |
| **Economia / Glosa Financeira Apurada** | **R$ 304,8 mil** evitados em pagamentos indevidos ou duplicados |
| **Chamados Operacionais Classificados via IA** | **45 chamados** triados em severidades `P1` a `P4` com cálculo de SLA |

---

## 🚀 Como Executar

```bash
python pipeline_automacao_corporativa.py
```

Os arquivos gerados ficam disponíveis imediatamente em:
* [`entregaveis_automacao/conciliacao_faturas_rpa.xlsx`](entregaveis_automacao/conciliacao_faturas_rpa.xlsx)
* [`entregaveis_automacao/relatorio_auditoria_rpa_e_ia.pdf`](entregaveis_automacao/relatorio_auditoria_rpa_e_ia.pdf)
* [`entregaveis_automacao/chamados_classificados_ia.json`](entregaveis_automacao/chamados_classificados_ia.json)
* [`cloud_s3_staging/manifesto_s3_sync.json`](cloud_s3_staging/manifesto_s3_sync.json)
