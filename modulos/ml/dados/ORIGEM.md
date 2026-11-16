# Origem dos dados — Modelagem Linear

## Arquivo original

- **Arquivo:** `epe_consumo_mensal_por_classe.xlsx`
- **Fonte:** EPE (Empresa de Pesquisa Energética), "Consumo mensal de energia elétrica por classe (regiões e subsistemas)"
- **Página:** https://www.epe.gov.br/pt/publicacoes-dados-abertos/publicacoes/consumo-de-energia-eletrica
- **Link do arquivo:** https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/Documents/CONSUMO%20MENSAL%20DE%20ENERGIA%20EL%C3%89TRICA%20POR%20CLASSE.xlsx
- **Data de acesso:** 14/11/2026
- **SHA-256 do arquivo baixado:** `177310f1182e285d6a1fa6379a8c85163fdb6bb22c488083a18300b7c8a24133`
- **Natureza:** dados reais publicados por órgão oficial (não são dados gerados ou fictícios).

O arquivo foi salvo sem nenhuma alteração. A EPE atualiza a planilha todo mês; uma versão baixada em outra data pode trazer meses a mais.

## Abas usadas

| Coluna da base | Aba da planilha | Unidade |
|---|---|---|
| consumo_total_mwh | CONSUMO POR UF | MWh |
| consumo_residencial_mwh | CONSUMO RESIDENCIAL POR UF | MWh |
| consumo_industrial_mwh | CONSUMO INDUSTRIAL POR UF | MWh |
| consumo_comercial_mwh | CONSUMO COMERCIAL POR UF | MWh |
| consumidores_residenciais | CONSUMIDORES RES. POR UF | unidades consumidoras |
| consumidores_comerciais | CONSUMIDORES COMERCIAIS POR UF | unidades consumidoras |

## Como a base organizada foi montada

Script: `modulos/ml/preparar_base.py`. Resultado: `base_consumo_uf_mensal.csv`.

1. Cada aba tem os anos e meses nas colunas e os 27 estados nas linhas. O script transforma isso em uma linha por estado e mês.
2. Mantém de janeiro de 2004 a dezembro de 2025 (7.128 linhas). Os meses de 2026 ficam de fora porque a planilha os marca como preliminares ("2026*").
3. Confere que não há valores ausentes nas colunas usadas.
4. Calcula as variáveis derivadas:
   - `consumo_medio_res_kwh` = consumo residencial (MWh) × 1000 ÷ consumidores residenciais
   - `consumo_medio_com_kwh` = consumo comercial (MWh) × 1000 ÷ consumidores comerciais
   - `participacao_industrial` = consumo industrial ÷ consumo total × 100

A planilha também tem o consumo do mercado livre, mas essa variável não foi usada porque não existe para vários estados em parte do período.
