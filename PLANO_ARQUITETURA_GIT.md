# PLANO DE ARQUITETURA DO REPOSITÓRIO GIT — ETH-WCMK

**Data:** 2026-11-15, 13:16 (America/Sao_Paulo) · **Referência:** rodada 5, núcleo v13, ontologia v4.2, corpus v7, paper v15.
**Base formal:** documentação oficial do GitHub ("Best practices for repositories", "Repository limits", "About releases", "About CITation files", "About Git LFS") e a estrutura observada nos repositórios de pesquisa mais avaliados: numpy (333k★), scikit-learn (68k★), pandas (50k★), sympy (15k★), Qiskit (8k★), astropy (5,4k★), biopython (5,3k★) e facebookresearch/cwm (919★ — artefato de pesquisa de referência para este tipo de projeto).

---

## 1. Diagnóstico medido (não estimativo)

| Métrica | Valor |
|---|---|
| Arquivos rastreados (HEAD) | 666 |
| Peso rastreado | **83,1 MB** na branch `main` limpa (1,83 GB na branch de desenvolvimento `master`) |
| `.git` | 227 MB |
| Blobs > 100 MB **no histórico** | 7 (até 498 MB) |
| Testes de invariants | 69 testes, 0 falhas, 45 s |
| Rodada r5 | 22 execuções, 51 artefatos com SHA-256, 65,9 MB |
| Corpora | 1.543 MB brutos → **104 MB comprimidos** (19 assets) |

Limites oficiais verificados na documentação do GitHub:

- objeto único: recomendado 1 MB, **limite enforced 100 MB** — push acima disso é rejeitado;
- push: até 2 GB; repositório: recomendado ≤ 10 GB em disco; 3.000 entradas por diretório; profundidade ≤ 50;
- **assets de release: até 2 GiB por arquivo, até 1.000 assets por release, sem limite total** — é o lugar certo para os corpora;
- Git LFS: 2 GB por arquivo (Free/Pro), quota de armazenamento e banda — desnecessário aqui.

**Conclusão:** publicar `master` como está falha no push. A solução não é perder dados: é separar código e artefatos pesados.

---

## 2. Arquitetura alvo

```
ETH-WCMK/
├── README.md                 ← porta de entrada (EN + resumo PT)
├── LICENSE                   ← MIT (texto padrão, detectável pelo GitHub)
├── LICENSE-CC-BY-SA-4.0.txt  ← termos do modelo/ontologia/texto
├── NOTICE                    ← atribuição + disclaimer
├── CITATION.cff              ← "Cite this repository" no sidebar
├── CHANGELOG.md              ← Keep a Changelog + SemVer
├── CONTRIBUTING.md           ← regras do projeto (frozen rounds, artefato por número)
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── .gitignore .gitattributes .editorconfig .pre-commit-config.yaml
├── Makefile pyproject.toml environment.yml requirements.txt requirements-dev.txt
├── .zenodo.json              ← metadados para DOI
├── .github/
│   ├── workflows/ci.yml               ← pytest + audit + manifest
│   ├── workflows/release-assets.yml   ← checksums em cada release
│   ├── ISSUE_TEMPLATE/{verification.yml, critique.yml}
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── ARCHITECTURE.md  REPRODUCIBILITY.md  DATA.md  GATES.md  PUBLISHING.md
│   └── PLANO_ARQUITETURA_GIT.md        ← este documento
├── data/CORPUS_MANIFEST.sha256         ← hashes de tudo que o paper usa
├── scripts/                            ← audit, manifest, assets, fetch, gate
├── _analysis/                          ← pipeline canônico (formal_core, corpus,
│                                         ontology, analysis, facets, paper)
├── Ontologias/ontology_v4_2/           ← TTL + SHACL + fixtures inválidos
├── Evaluacoes/r2…r5/                   ← rodadas congeladas + manifests
└── paper/                              ← figuras, equations, DOCX
```

### Política de dados (3 tiers)

| Tier | Conteúdo | Onde | Tamanho |
|---|---|---|---|
| **A — git plain** | código, docs, configs, manifests, registries, JSON agregado < 5 MB, figuras, módulos TTL | repositório | ≈ 49 MB |
| **B — GitHub Release** | corpora `.jsonl.gz`, grafos de instância `.ttl.gz` | tag `v13.0.0` | 104 MB |
| **C — Zenodo** | snapshot versionado com DOI | espelho de B | espelho de B |

Justificativa: (1) GitHub rejeita objetos > 100 MB; (2) LFS consome quota de banda a cada clone; (3) releases aceitam 2 GiB por arquivo sem limite total; (4) DOI é exigência FAIR e da maioria dos periódicos. Os corpora são deterministas (`SEED = 20261104` registrado dentro do artefato), logo publicar os bytes exatos é suficiente para reproduzir tudo.

---

## 3. Higiene de histórico (decisão obrigatória antes do push)

O `.git` atual contém blobs de 498 MB. Três caminhos:

1. **Branch `main` órfã** (já criada: 666 arquivos, 83 MB, sem blobs pesados). Publica-se só ela. Desenvolvimento continua em `master` local ou em repositório privado. → **recomendado, não destrutivo.**
2. **Reescrita com `git filter-repo`** removendo `Evaluacoes/**/corpus_*confrontations.jsonl`, `*gold.jsonl`, `Ontologias/**/instances.ttl`, `.cache_validation`. Mantém os 17 commits, elimina os blobs. Requer backup.
3. **Repositório novo** com histórico reconstruído por gates. Menos fiel.

Nunca publicar sem rodar `./scripts/publish_check.sh`.

---

## 4. Checklist de documentação (padrão dos repos bem avaliados)

| Requisito | Situação |
|---|---|
| README com abstract, quickstart, mapa, citation, licença, limitações | ✅ |
| LICENSE detectável + NOTICE + termos CC | ✅ |
| CITATION.cff com `preferred-citation` | ✅ (falta DOI/ORCID) |
| CHANGELOG, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY | ✅ |
| Issue/PR templates | ✅ |
| CI (69 invariantes + audit + manifest) | ✅ |
| `.gitignore`, `.gitattributes`, `.editorconfig`, pre-commit | ✅ |
| Ambiente reprodutível (`requirements.txt` + `environment.yml`) | ✅ |
| Releases com assets e checksums | ⬜ (fazer no GitHub) |
| DOI (Zenodo) | ⬜ |
| Descrição, tópicos, homepage na seção "About" | ⬜ |
| Branch protection + CODEOWNERS | ⬜ |
| Testes em diretório dedicado / pacote instalável | ⬜ (fase 2) |

---

## 5. Versionamento

- `v13.0.0` = núcleo v13 / ontologia v4.2 / corpus v7.
- major = mudança do núcleo aritmético que altera vereditos (ex.: S₄ de Gödel, α derivada); minor = novas baterias/corpora; patch = documentação/correções de texto.
- Cada tag gera release com `ASSET_MANIFEST.json` + corpora comprimidos.

---

## 6. Fases

| Fase | Ação | Verificação |
|---|---|---|
| 0 | Backup (`git bundle`) | `git bundle verify` |
| 1 | Camada de publicação no root | `./scripts/publish_check.sh` → READY |
| 2 | Corpora fora do tracking | `python3 scripts/audit_repo.py` → 0 bloqueadores |
| 3 | Criar repo no GitHub e configurar About/topics/branch protection | settings do repo |
| 4 | Push da branch limpa | push ≈ 83 MB, sem rejeição |
| 5 | Release `v13.0.0` com 19 assets (104 MB) | download + `scripts/fetch_data.py --local release_assets` |
| 6 | Zenodo + DOI, ORCID, badges no README | DOI aparece no CITATION.cff |
| 7 | (opcional) Fase 2: `src/ethwcmk/` + `tests/`, mkdocs, CodeQL | CI verde |

---

## 7. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Push rejeitado | branch órfã limpa ou `filter-repo` |
| Reviewer não encontra os dados | README + docs/DATA.md + manifest verificável |
| Números do paper divergem do código | CI roda os 69 testes + o verificador paper↔artefato |
| Repo pesado para contribuir | tier A ≈ 49 MB; corpora fora do clone |
| Licença ambígua (dual) | LICENSE MIT padrão + NOTICE + arquivo CC separado |
| Perda de contexto de pesquisa | rodadas congeladas e manifests permanecem no repo |

---

## 8. Decisões (fechadas em 15/11/2026)

1. **Owner**: organização `ETH-WCMK`. GitHub não expõe criação de organização para contas comuns pela API (POST /orgs devolve 404); é preciso criá-la pelo navegador em <https://github.com/orgs/new>. Até lá o repo vive em `Palazzo13-X/ETH-WCMK` e será transferido — GitHub preserv releases, estrelas, issues e faz redirect do URL antigo.
2. **Idioma do README**: EN principal + resumo PT (implementado).
3. **Corpora**: GitHub Releases (+ Zenodo depois), não Git LFS.
4. **ORCID**: Palazzo `0009-0008-0833-3463`; Vanzin `0000-0001-8121-8398` — já em `CITATION.cff` e `.zenodo.json`.
5. **Histórico**: branch órfã limpa (`main`); `master` continua local, com backup em bundle.
6. **Paper DOCX**: não anexado ao release até o depósito no arXiv.
7. **r2/r3**: permanecem no repo (46,4 MB de corpora congelados).
8. **Site de documentação**: fase 2, depois do DOI.

## 9. Estado de execução (15/11/2026, 17:40 BRT)

| Item | Estado |
|---|---|
| Repositório público criado | `https://github.com/Palazzo13-X/ETH-WCMK` |
| Branch `main` limpa (1 commit, 673 arquivos, 122,3 MB, nenhum blob > 100 MB) | publicada |
| Descrição, 13 tópicos, issues, wiki/projects | configurados |
| `main` protegida | feita |
| Release `v13.0.0` com 20 assets (104,5 MB) | publicado |
| Labels de issue e Dependabot | criados |
| CI Actions | arquivos em `ci/`; instalar exige o escopo `workflow` (`gh auth refresh -h github.com -s workflow` → `./scripts/push_ci.sh`) |
| Organização `ETH-WCMK` + transferência do repo | pendente (1 passo manual) |
| Zenodo / DOI | pendente |
