#!/usr/bin/env python3
"""Pipeline de Automação de Processos Corporativos (RPA/ETL), Integração de APIs, IA e Cloud AWS S3.

Execução:
    python pipeline_automacao_corporativa.py

O que este robô de automação executa de ponta a ponta:
  1. Ingestão Multi-Fonte & API REST:
     - Consulta a API oficial PTAX do Banco Central do Brasil (com fallback resiliente offline)
       para obter a taxa de câmbio USD/BRL na conciliação de faturas internacionais de Cloud/SaaS.
     - Lê lotes de Faturas de Fornecedores (CSV/Excel) e Chamados Operacionais de Service Desk (JSON).
  2. Conciliação Financeira Automatizada (RPA Backoffice):
     - Audita automaticamente divergências entre o valor contratado e o valor cobrado em cada fatura,
       identificando cobranças indevidas, duplicidades e variações cambiais acima da tolerância (5%).
  3. Motor de Classificação Inteligente (IA / NLP Rules & LLM-Ready Prompting):
     - Analisa o texto livre de chamados operacionais, classifica a categoria, a severidade (P1 a P4),
       detecta risco de violação de SLA e recomenda ação imediata.
  4. Geração de Entregáveis Auditados & Sincronização Cloud (AWS S3 / boto3):
     - Exporta planilha de conciliação e SLA em Excel (.xlsx) e relatório de auditoria em PDF (.pdf).
     - Prepara e sincroniza o lote auditado com bucket AWS S3 (via `boto3` quando credenciais AWS
       estão configuradas ou em diretório de staging S3 local).
"""
from __future__ import annotations

import csv
import json
import os
import pathlib
import random
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from pdf_simples import escrever_pdf  # noqa: E402
from xlsx_simples import escrever_xlsx  # noqa: E402


def consultar_ptax_bacen(data_mm_dd_yyyy: str = "10-16-2026") -> tuple[float, str]:
    """Consulta cotação PTAX USD/BRL na API Olinda do Banco Central (com fallback determinístico)."""
    url = (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        f"CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='{data_mm_dd_yyyy}'&$top=1&$format=json"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EnterpriseAutomationBot/1.0"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
            if dados.get("value"):
                return float(dados["value"][0]["cotacaoVenda"]), "API Olinda BACEN (Online)"
    except Exception:
        pass
    return 5.6542, "Cache Resiliente BACEN PTAX (Offline/Determinístico)"


def gerar_entradas_operacionais(pasta_in: pathlib.Path, seed: int = 42) -> None:
    rng = random.Random(seed)
    pasta_in.mkdir(parents=True, exist_ok=True)

    fornecedores = [
        ("FORN-01", "AWS Cloud Services", "USD", 12500.00),
        ("FORN-02", "Databricks Lakehouse", "USD", 8400.00),
        ("FORN-03", "Microsoft Azure Enterprise", "USD", 9200.00),
        ("FORN-04", "CodeForge Tech Consultoria", "BRL", 48000.00),
        ("FORN-05", "Telecom Fibra Corporativa", "BRL", 14200.00),
        ("FORN-06", "SaaS CRM & Automação", "USD", 3800.00),
    ]

    faturas = []
    for i in range(1, 61):
        fid = f"FAT-2026-{i:03d}"
        cod, nome, moeda, valor_contrato = rng.choice(fornecedores)
        anomalia = rng.choices(
            ["OK", "COBRANCA_ACIMA_CONTRATO", "DUPLICIDADE_SUSPEITA", "TAXA_CAMBIO_DIVERGENTE"],
            weights=[0.74, 0.14, 0.06, 0.06]
        )[0]
        fator = 1.0
        if anomalia == "COBRANCA_ACIMA_CONTRATO":
            fator = rng.uniform(1.12, 1.28)
        elif anomalia == "TAXA_CAMBIO_DIVERGENTE":
            fator = rng.uniform(1.07, 1.11)

        valor_cobrado = round(valor_contrato * fator, 2)
        faturas.append({
            "id_fatura": fid,
            "codigo_fornecedor": cod,
            "fornecedor": nome,
            "moeda": moeda,
            "valor_contratado_original": valor_contrato,
            "valor_faturado_original": valor_cobrado,
            "vencimento": f"2026-10-{rng.randint(18, 30):02d}",
            "nota_fiscal_hash": f"NF-{rng.randint(10000, 99999)}" if anomalia != "DUPLICIDADE_SUSPEITA" else "NF-DUPLICADA-9901",
        })

    with (pasta_in / "faturas_fornecedores.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(faturas[0].keys()))
        w.writeheader()
        w.writerows(faturas)

    exemplos_chamados = [
        ("Erro de timeout na integração da API de faturamento S3 na madrugada", "Infra & Cloud"),
        ("Divergência no relatório DRE do fechamento contábil mensal no BI", "Dados & BI"),
        ("Robô RPA de conciliação bancária parou por alteração de layout XML", "Automação RPA"),
        ("Solicitação de liberação de acesso IAM para novo analista de dados", "Segurança & IAM"),
        ("Queda de performance e fila lenta no processamento de pagamentos Pix", "Crítico / Produção"),
        ("Dúvida sobre filtro de safra no painel executivo da diretoria", "Suporte BI"),
    ]
    chamados = []
    for i in range(1, 46):
        desc, area = rng.choice(exemplos_chamados)
        tempo_aberto_h = rng.randint(1, 36)
        chamados.append({
            "id_chamado": f"INC-{4000 + i}",
            "area_solicitante": area,
            "descricao_livre": desc,
            "horas_em_aberto": tempo_aberto_h,
        })

    (pasta_in / "chamados_operacionais.json").write_text(
        json.dumps(chamados, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def classificar_chamado_ia(descricao: str, horas_aberto: int) -> dict:
    """Classificador inteligente determinístico (NLP keyword scoring + regras de SLA)."""
    txt = descricao.lower()
    if any(k in txt for k in ("queda", "timeout", "parou", "pix", "erro")):
        prioridade = "P1 - Crítico"
        sla_max_h = 4
        acao = "Acionar Plantão SRE / Engenharia de Automação Imediatamente"
    elif any(k in txt for k in ("divergência", "fechamento", "layout")):
        prioridade = "P2 - Alta"
        sla_max_h = 8
        acao = "Priorizar na Sprint Diária de Dados & RPA"
    elif "acesso" in txt or "iam" in txt:
        prioridade = "P3 - Média"
        sla_max_h = 24
        acao = "Executar Provisionamento Automatizado via IAM Role"
    else:
        prioridade = "P4 - Baixa"
        sla_max_h = 48
        acao = "Responder com Base de Conhecimento Automatizada"

    violou_sla = horas_aberto > sla_max_h
    return {
        "prioridade_ia": prioridade,
        "sla_alvo_horas": sla_max_h,
        "status_sla": "SLA VIOLADO" if violou_sla else "DENTRO DO SLA",
        "acao_recomendada": acao,
    }


def sincronizar_cloud_s3(arquivos: list[pathlib.Path], pasta_staging_s3: pathlib.Path) -> str:
    """Sincroniza entregáveis com AWS S3 via boto3 (ou grava manifesto S3 local se offline)."""
    bucket = os.environ.get("AWS_S3_BUCKET_AUTOMACAO", "")
    pasta_staging_s3.mkdir(parents=True, exist_ok=True)
    manifesto = {
        "destino_cloud": f"s3://{bucket}/automacao_backoffice/" if bucket else "local_s3_staging/automacao_backoffice/",
        "arquivos_sincronizados": [a.name for a in arquivos],
        "status_sincronizacao": "OK",
    }
    if bucket:
        try:
            import boto3  # type: ignore
            s3 = boto3.client("s3")
            for arq in arquivos:
                s3.upload_file(str(arq), bucket, f"automacao_backoffice/{arq.name}")
            manifesto["modo"] = "AWS S3 Real (boto3)"
        except Exception as exc:
            manifesto["modo"] = f"Staging Local (Fallback: {exc})"
    else:
        manifesto["modo"] = "Staging Cloud Local (Pronto para AWS S3 boto3)"

    caminho_manifesto = pasta_staging_s3 / "manifesto_s3_sync.json"
    caminho_manifesto.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifesto["modo"]


def executar_pipeline() -> dict:
    pasta_in = RAIZ / "dados_entrada"
    pasta_out = RAIZ / "entregaveis_automacao"
    pasta_s3 = RAIZ / "cloud_s3_staging"

    gerar_entradas_operacionais(pasta_in, seed=42)
    ptax, fonte_ptax = consultar_ptax_bacen()

    # 1. Conciliação de Faturas
    with (pasta_in / "faturas_fornecedores.csv").open(encoding="utf-8") as f:
        faturas = list(csv.DictReader(f))

    linhas_faturas_xlsx = [[
        "ID Fatura", "Fornecedor", "Moeda", "Cotação PTAX",
        "Contratado (BRL)", "Faturado (BRL)", "Diferença (BRL)", "Status Auditoria RPA"
    ]]
    total_faturado_brl = 0.0
    glosa_recuperavel_brl = 0.0
    faturas_bloqueadas = 0

    for fat in faturas:
        taxa = ptax if fat["moeda"] == "USD" else 1.0
        contratado_brl = round(float(fat["valor_contratado_original"]) * taxa, 2)
        faturado_brl = round(float(fat["valor_faturado_original"]) * taxa, 2)
        dif = round(faturado_brl - contratado_brl, 2)
        total_faturado_brl += faturado_brl

        if fat["nota_fiscal_hash"] == "NF-DUPLICADA-9901":
            status_aud = "BLOQUEADA - DUPLICIDADE NF"
            faturas_bloqueadas += 1
            glosa_recuperavel_brl += faturado_brl
        elif dif > contratado_brl * 0.05:
            status_aud = "BLOQUEADA - COBRANÇA EXCEDENTE (>5%)"
            faturas_bloqueadas += 1
            glosa_recuperavel_brl += dif
        else:
            status_aud = "APROVADA PARA PAGAMENTO"

        linhas_faturas_xlsx.append([
            fat["id_fatura"], fat["fornecedor"], fat["moeda"], round(taxa, 4),
            contratado_brl, faturado_brl, dif, status_aud
        ])

    # 2. Classificação Inteligente de Chamados
    chamados = json.loads((pasta_in / "chamados_operacionais.json").read_text(encoding="utf-8"))
    criticos_p1 = 0
    slas_violados = 0
    for ch in chamados:
        res_ia = classificar_chamado_ia(ch["descricao_livre"], int(ch["horas_em_aberto"]))
        ch.update(res_ia)
        if res_ia["prioridade_ia"].startswith("P1"):
            criticos_p1 += 1
        if res_ia["status_sla"] == "SLA VIOLADO":
            slas_violados += 1

    pasta_out.mkdir(parents=True, exist_ok=True)
    caminho_xlsx = pasta_out / "conciliacao_faturas_rpa.xlsx"
    escrever_xlsx(caminho_xlsx, linhas_faturas_xlsx, aba="Auditoria_Faturas")

    caminho_chamados_json = pasta_out / "chamados_classificados_ia.json"
    caminho_chamados_json.write_text(json.dumps(chamados, ensure_ascii=False, indent=2), encoding="utf-8")

    blocos_pdf = [
        ("titulo", "Relatorio de Automacao Corporativa (RPA), Conciliacao e Triagem com IA"),
        ("subtitulo", f"Cotacao PTAX utilizada: R$ {ptax:.4f} ({fonte_ptax})"),
        ("espaco", ""),
        ("subtitulo", "1. CONCILIACAO AUTOMATIZADA DE FATURAS E CONTRATOS (FINOPS & BACKOFFICE)"),
        ("normal", f"Total de faturas processadas pelo robo: {len(faturas)} faturas (R$ {total_faturado_brl:,.2f})."),
        ("normal", f"Faturas bloqueadas automaticamente por divergencia ou duplicidade: {faturas_bloqueadas} faturas."),
        ("normal", f"Economia / Glosa apurada pelo robo antes do pagamento: R$ {glosa_recuperavel_brl:,.2f}."),
        ("espaco", ""),
        ("subtitulo", "2. TRIAGEM INTELIGENTE DE CHAMADOS OPERACIONAIS COM IA (SERVICE DESK)"),
        ("normal", f"Total de chamados classificados automaticamente: {len(chamados)} chamados."),
        ("normal", f"Incidentes criticos (P1) detectados: {criticos_p1} | Alertas de SLA violado: {slas_violados}."),
    ]
    caminho_pdf = pasta_out / "relatorio_auditoria_rpa_e_ia.pdf"
    escrever_pdf(caminho_pdf, blocos_pdf)

    modo_s3 = sincronizar_cloud_s3([caminho_xlsx, caminho_pdf, caminho_chamados_json], pasta_s3)

    return {
        "cotacao_ptax_usd_brl": ptax,
        "faturas_processadas": len(faturas),
        "faturas_bloqueadas_rpa": faturas_bloqueadas,
        "economia_glosa_reais": round(glosa_recuperavel_brl, 2),
        "chamados_triados_ia": len(chamados),
        "cloud_sync": modo_s3,
        "xlsx": str(caminho_xlsx),
        "pdf": str(caminho_pdf),
    }


if __name__ == "__main__":
    resumo = executar_pipeline()
    print("Automação de processos concluída com sucesso!")
    for k, v in resumo.items():
        print(f"  {k:<24}: {v}")
