# Auditoria de ontologia — `wcmk-facets.ttl` + `wcmk-facets.shacl.ttl` vs. catálogo v1

**Base auditada:** `wcmk-facets.ttl` (31.770 B, 603 linhas), `wcmk-facets.shacl.ttl` (18.064 B, 461 linhas), `_analysis/facets_catalog_v1.txt` (51.940 B, 461 linhas). Namespaces: `wcmkf:` = `https://ethwcmk.org/ontology/wcmk-facets#`, `shapes:` = `https://ethwcmk.org/shapes/wcmk-facets#`. Ontologia: `owl:label "WCMK Facets Ontology (Draft v0.1)"`, `owl:versionInfo "0.1-draft"`.
**Evidência de conformidade (PyShACL + rdflib 7.6.0):** `conforms: True`, `violations: 0`. Mas a conformidade é *vacuosa* em nível de dados: 0 indivíduos de `FacetAssessment`, `FacetRequirement`, `FacetDeficit`, `FacetizedAgencyProfile`, `CalibrationArtifact` no TTL.

---

## A — Inventário exacto das facetas definidas

Nenhuma faceta declara β nem θ: `hasWeight` existe como propriedade, mas **0 instâncias no TTL**; θ só existe como string numérica embutida em SPARQL (`< 0.20`) e como `minimumRequiredLevel` em instâncias de exemplo.

| Cód | Classe (`wcmkf:`) | prefLabel pt-BR | Vértice | Definição (`skos:definition`) | Observáveis (catálogo) | Política de agregação (TTL) | θ |
|---|---|---|---|---|---|---|---|
| W1 | GoalOrientation | Orientação a objetivos | WantVertex | "Purpose toward which the agent action is directed." | objetivo declarado; métricas-alvo do serviço | WeightedMeanCompensatory | — |
| W2 | ValueAlignment | Alinhamento axiológico | Want | "Alignment of the pursued end with protected values and ethical commitments." | aderência a princípios (PBIA/UNESCO/OECD) | GuardedWeightedMean | — |
| W3 | StakeholderRegard | Consideração de stakeholders | Want | "Recognition of affected parties, including indirect and vulnerable stakeholders." | grupos vulneráveis; externalidades | GuardedWeightedMean | — |
| W4 | PriorityDiscipline | Disciplina de prioridades | Want | "Capacity to order competing goals under ethical precedence rules." | regras de precedência; trade-offs | GuardedWeightedMean | — |
| W5 | IntentionalStability | Estabilidade intencional | Want | "Stability of the practical orientation under domain and situational variation." | variância de metas em cenários próximos | WeightedMeanCompensatory | — |
| C1 | FunctionalCapability | Capacidade funcional | Can | "Operational ability to perform the target function." | taxa de sucesso; completude | WeightedMeanCompensatory | — |
| C2 | Robustness | Robustez | Can | "Resilience against noise, drift, missing information and adversarial variation." | testes adversariais; degradação OOD | GuardedWeightedMean | — |
| C3 | Controllability | Controlabilidade | Can | "Degree to which the system remains governable during operation." | kill switch; aprovação humana; logs | ThresholdOverride | — |
| C4 | ScopeAdequacy | Adequação de escopo | Can | "Fitness of the agent capabilities to the scope and complexity of the case." | out-of-scope detection | GuardedWeightedMean | — |
| C5 | ResourceSufficiency | Suficiência de recursos | Can | "Sufficiency of resources needed to act safely and effectively." | tempo de resposta; orçamento | WeightedMeanCompensatory | — |
| C6 | SafeExecutability | Executabilidade segura | Can | "Whether action can be carried out without creating excessive secondary harms." | simulações de falha; reversibilidade | ThresholdOverride | 0.20 (Warning) |
| M1 | LegalObligation | Obrigação legal | Must | "Normative requirements grounded in the legal-regulatory layer." | leis; standards mandatórios | ThresholdOverride | 0.20 (Warning) |
| M2 | InstitutionalPolicyObligation | Obrigação de policy institucional | Must | "Requirements imposed by institutional policy and governance instruments." | playbooks; fluxos de autorização | GuardedWeightedMean | — |
| M3 | EthicalPrincipleObligation | Obrigação por princípio ético | Must | "Requirements justified by principles that may exceed legal and policy minima." | justificabilidade; balanceamento | GuardedWeightedMean | — |
| M4 | PrudentialObligation | Obrigação prudencial | Must | "Context-sensitive duty of caution under elevated moral uncertainty or potential harm." | escalonamento; "limiar de confiança" | ThresholdOverride | 0.20 (Warning) |
| M5 | RoleObligation | Obrigação de papel | Must | "Normative commitments attached to institutional or functional role." | alçada; dever de encaminhar | GuardedWeightedMean | — |
| M6 | AccountabilityObligation | Obrigação de accountability | Must | "Requirements related to auditability, traceability and accountability." | logs; reprodutibilidade do fluxo | ThresholdOverride | — |
| K1 | EvidentialKnowledge | Conhecimento evidencial | Know | "Factual or evidential basis supporting the decision." | qualidade das fontes | WeightedMeanCompensatory | — |
| K2 | ContextualKnowledge | Conhecimento contextual | Know | "Knowledge of the circumstances that give meaning to the case." | sensibilidade temporal | GuardedWeightedMean | — |
| K3 | NormativeKnowledge | Conhecimento normativo | Know | "Knowledge of what norms apply and how they constrain action." | detecção de conflito normativo | GuardedWeightedMean | — |
| K4 | ProceduralKnowledge | Conhecimento procedimental | Know | "Know-how required to operationalize a justified course of action." | checkpoints; sequência | WeightedMeanCompensatory | — |
| K5 | CausalKnowledge | Conhecimento causal | Know | "Knowledge of causal structure and consequences of action." | feedback loops; segunda ordem | GuardedWeightedMean | — |
| K6 | UncertaintyAwareness | Consciência de incerteza | Know | "Meta-knowledge concerning uncertainty, ignorance and confidence limits." | scores de confiança; fallback | UncertaintyPenalizedMean | 0.20 (Warning) |
| K7 | ProvenanceAwareness | Consciência de proveniência | Know | "Knowledge of where information came from and how trustworthy it is." | linhagem de dado; versão de policy | GuardedWeightedMean | — |

**A.1 Distribuição das políticas (l. 516–542):** `GuardedWeightedMean` 12, `WeightedMeanCompensatory` 6, `ThresholdOverride` 5, `UncertaintyPenalizedMean` 1, `SoftMinPenalty` **0** (o indivíduo existe — l. 500 — e `"soft_min"` está no `sh:in`, mas nenhuma faceta o usa). `allowsCompensation`: WMC/GWM/UPM = `true`; TO/SoftMin = `false`.
**Incoerência catálogo ↔ TTL:** o catálogo (l. 214) pede para W4 "uma política lexicográfica ou de pisos prudenciais" e para K6 "candidata a gate prudencial… deve penalizar fortemente Aa"; a TTL atribui a W4 `GuardedWeightedMean` (compensatório) e a K6 `UncertaintyPenalizedMean` (compensatório). Não existem modos `lexicographic` nem `hard_gate` na enumeração SHACL.
**A.2 Onde existem pesos e limiares reais:** apenas em `bridge-wcmkplus-scoring-example-valid.ttl`: 24 `wcmkf:FacetRequirement` com `wcmkf:hasWeight "0.80"^^xsd:decimal` (l. 229–574 — **todos iguais**, β uniforme) e `minimumRequiredLevel` distribuído entre 0.70 e 0.85 (0.70×2, 0.72×3, 0.74×3, 0.76×3, 0.78×3, … max 0.85). As propriedades de limiar do bridge — `bridge:thresholdRcHi`, `bridge:thresholdAaAllow`, `bridge:thresholdAaGuards` (bridge-wcmkplus.ttl l. 182–190) — estão declaradas mas **nunca instanciadas** em nenhum arquivo.

---

## B — Contagem e divergências TTL ↔ catálogo

- **Total: 24 (não 26)** em ambos. Decomposição: 5 Want + 6 Can + 6 Must + 7 Know. Confirmado por `grep -c "projectsToCoreVertex wcmkf:"` = 24, `owl:Class` = 37 (13 classes estruturais + 24 de facetas), axiom `owl:minQualifiedCardinality "24"^^xsd:nonNegativeInteger` (l. 257) e `sh:minCount 24` sobre `hasAssessment` (SHAACL l. 317) + SPARQL `HAVING (?n < 5)`, `(?n < 6)`, `(?n < 6)`, `(?n < 7)`.
- **Nomenclatura:** 22/24 nomes coincidem. Divergências: W1 catálogo "Orientação finalística" vs TTL `skos:prefLabel "Orientação a objetivos"@pt-BR`; K6 catálogo "Metaconhecimento e consciência de incerteza" vs TTL `"Consciência de incerteza"@pt-BR`.
- **Prefixo:** o catálogo sugere `wcmk:GoalOrientation`, `wcmk:FacetScore`; a TTL implementa `wcmkf:`. Nenhum arquivo do corpus declara o IRI `https://ethwcmk.org/ontology/wcmk#` como prefixo de facetas.
- **Domínios:** catálogo lista **10** (Saúde, Justiça e Segurança, Infraestrutura Crítica, Finanças, Governança Pública, Privacidade e Dados, Informação e Mídia, Educação, Trabalho, Meio Ambiente e Energia). TTL implementa **4** indivíduos `DomainProfile` (l. 548–560): `HealthDomainProfile`, `JusticeSecurityDomainProfile`, `CriticalInfrastructureDomainProfile`, `EducationDomainProfile`. Falta módulo inteiro previsto no catálogo: `wcmk-domain-profiles.ttl` ("pesos, criticidades, thresholds") — não existe na pasta.
- **Criticidade:** apenas **6 triples** `isCriticalInDomain` (l. 568–573) cobrindo 6 facetas ⇒ **18/24 sem criticidade declarada** (12 pares faceta–domínio no total, contra dezenas sugeridas na Tabela 1). Ex.: C3 Controlabilidade é "crítica" em 7 domínios no catálogo, mas só existe em 3 perfis.
- **Elementos prometidos e ausentes:** `wcmk:FacetScore`/`hasFacetScore`/`hasNumericScore` → substituídos por `FacetAssessment` + `hasNormalizedScore`; `wcmk:NonCompensatoryGate` → `ThresholdOverride`; `requiresHumanReview` existe só em `bridge-architecture-v2.ttl:29` e `ethcase-analysis.ttl:26`, não na ontologia de facetas; `derivedFromCalibrationRun` → `usesCalibrationArtifact`. Dos 72 nomes de "Propriedades centrais" sugeridos, **só `projectsToCoreVertex` e `prov:wasDerivedFrom` existem**; testados 31 (`hasStatedGoal`, `hasCapabilityScore`, `isReversible`, `hasAuditTrail`, `subjectToLaw`, `requiresPrudentialGuard`, `knowsApplicableNorm`, `hasCausalCoverage`, `recognizesUnknown`, `hasPolicyVersion`…) → **0 ocorrências** em todo o corpus.

---

## C — Estrutura SHACL exacta

15 shapes (14 `sh:NodeShape` + 1 `sh:PropertyShape`), **31 blocos `sh:property`**, **8 `sh:sparql`**, 17 `sh:minCount`, 15 `sh:maxCount`, 9 `sh:hasValue`, 11 `sh:datatype`, 8 `sh:minInclusive`/8 `sh:maxInclusive`, **0 `sh:pattern`**.

| Shape (linha) | Alvo | Restrições |
|---|---|---|
| `FacetReferenceShape` (22) | usado por outras shapes | `projectsToCoreVertex` min 1 **max 1**; `hasAggregationPolicy` min 1 max 1; `skos:prefLabel` min 1; `skos:definition` min 1 |
| `DecimalUnitIntervalPropertyShape` (48) | *nenhum* (`a sh:PropertyShape` isolada) | xsd:decimal, [0,1] — **shape morta**, nunca referenciada |
| `FacetDefinitionShape` (60) | `sh:targetSubjectsOf wcmkf:projectsToCoreVertex` | `rdf:type` hasValue `owl:Class`; `rdfs:subClassOf` min 1; `sh:node FacetReferenceShape` |
| `Want/Can/Must/KnowFacetDefinitionShape` (76/92/108/125) | listas fechadas de `sh:targetNode` (5, 6, 6, 7 IRIs) | `subClassOf` hasValue `<Pillar>Facet`; `projectsToCoreVertex` hasValue `<Pillar>Vertex` |
| `AggregationPolicyShape` (146) | `wcmkf:AggregationPolicy` | `aggregationMode` 1×, string, `sh:in ("weighted_mean","guarded_weighted_mean","threshold_override","soft_min","uncertainty_penalized_mean")`; `allowsCompensation` 1× boolean |
| `FacetAssessmentShape` (170) | `wcmkf:FacetAssessment` | `assessesFacet` 1× IRI + `FacetReferenceShape`; `hasNormalizedScore` 1× decimal [0,1]; `hasConfidence` **max 1 (opcional)**; `usesCalibrationArtifact` `sh:class CalibrationArtifact`; `prov:wasDerivedFrom` IRI |
| `FacetRequirementShape` (211) | `wcmkf:FacetRequirement` | `requiresFacet` 1×; `minimumRequiredLevel` 1× [0,1]; `hasWeight` max 1 [0,1]; `criticalityLevel` max 1, `sh:in ("critical","high","medium","low")` |
| `FacetDeficitShape` (248) | `wcmkf:FacetDeficit` | `concernsFacet` 1×; `observedLevel` 1× [0,1]; `requiredLevel` 1× [0,1]; `deficitValue` 1× [0,1]; SPARQL: `BIND(IF((?r - ?o) > 0, (?r - ?o), 0.0) AS ?expected) FILTER (ABS(?dv - ?expected) > 0.000001)` |
| `FacetizedAgencyProfileShape` (309) | `wcmkf:FacetizedAgencyProfile` | `hasAssessment` **minCount 24** (sem maxCount); 4 SPARQL: ≥5 Want, ≥6 Can, ≥6 Must, ≥7 Know (`?facet rdfs:subClassOf* wcmkf:WantFacet … HAVING (?n < 5)`); 1 SPARQL anti-duplicação |
| `DomainProfileShape` (412) | `wcmkf:DomainProfile` | `[ sh:inversePath wcmkf:isCriticalInDomain ]` minCount 1 |
| `CriticalLowScoreWarningShape` (426) | `FacetAssessment`, `sh:severity sh:Warning` | `FILTER (?facet IN (wcmkf:LegalObligation, wcmkf:PrudentialObligation, wcmkf:UncertaintyAwareness)) FILTER (xsd:decimal(?score) < 0.20)` |
| `UnsafeExecutabilityWarningShape` (445) | `FacetAssessment`, Warning | `assessesFacet wcmkf:SafeExecutability … FILTER (xsd:decimal(?score) < 0.20)` |

**Restrições que bloqueiam/problematizam:**
1. **`sh:maxCount 1` em `wcmkf:projectsToCoreVertex`** (`"A facet reference must project to exactly one WCMK core vertex."`) + `sh:hasValue wcmkf:<Pillar>Vertex` + axiom `owl:AllDisjointClasses (WantFacet, CanFacet, MustFacet, KnowFacet)` (l. 598–599) ⇒ uma faceta não pode contribuir a dois pilares: **compartilhamento multi-pilar é estruturalmente proibido**.
2. **Mundo fechado:** os 4 pilares usam `sh:targetNode` enumerando as 24 IRIs. Uma 25ª faceta não seria validada por nenhuma shape de pilar.
3. **`projectsToCoreVertex` não tem `sh:in`** sobre os 4 vértices: qualquer IRI (não-vertex) passa; só as 24 IRIs enumeradas estão ancoradas por `hasValue`.
4. **θ hardcoded e não recalibrável:** 0.20 aparece literalemente em duas shapes, sem propriedade de limiar, sem ligação a `DomainProfile`, e apenas para 4 das 24 facetas. `ThresholdOverride` é declarado para C3 e M6 sem nenhum limiar ⇒ guarda inerte.
5. **Inconsistência OWL ↔ SHACL:** o axiom `minQualifiedCardinality 24` se aplica a `wcmkf:hasFacet`, mas a shape exige minCount 24 de `wcmkf:hasAssessment` e **não impõe nenhuma restrição sobre `hasFacet`** ⇒ perfis conformes em SHACL podem violar o axiom OWL, e vice-versa.
6. **Contradição interna:** `hasAssessment` aceita 24+ avaliações sem `maxCount`, enquanto a SPARQL anti-duplicação afirma que o perfil "should not assess the same facet more than once". A shape usa `sh:sparql` sem `sh:severity`, logo o "should" é **violação de severidade normal** (bloqueante) — wording e enforcement divergem.
7. **`hasNormalizedScore` é obrigatório (min 1), `hasConfidence` opcional** ⇒ `UncertaintyPenalizedMean` não é computável para avaliações sem confiança (K6).

---

## D — Classes, hierarquia, domínios/ranges e indivíduos

**Hierarquia:** `CoreVertex`; `Facet` → `WantFacet`/`CanFacet`/`MustFacet`/`KnowFacet` (disjuntas); `FacetAssessment ⊂ prov:Entity`, `FacetRequirement ⊂ prov:Entity`, `FacetDeficit ⊂ prov:Entity`, `CalibrationArtifact ⊂ prov:Entity`; `FacetizedAgencyProfile`, `AggregationPolicy`, `DomainProfile` sem superclasse.
**14 propriedades de objeto:** `projectsToCoreVertex` (Facet → CoreVertex), `hasFacet`, `hasAssessment`, `assessesFacet` (FacetAssessment → Facet), `hasRequirement`, `requiresFacet`, `hasDeficit`, `concernsFacet`, `hasAggregationPolicy` (Facet → AggregationPolicy), `isCriticalInDomain` (Facet → DomainProfile), `usesCalibrationArtifact`, e 3 "hooks" sem efeito funcional: `facetizedProjectionToCanonicalScore` (domínio `FacetizedAgencyProfile`, **sem range, sem shape**), `derivedFromCaseRequirement`, `usedInConfrontation`.
**10 propriedades de datatype:** `hasNormalizedScore`, `hasConfidence`, `minimumRequiredLevel`, `observedLevel`, `requiredLevel`, `deficitValue`, `criticalityLevel` (string), `aggregationMode` (string), `allowsCompensation` (boolean), `hasWeight` (**sem domínio declarado**: "Generic weight used by a profile, requirement or aggregation policy").
**Indivíduos declarados (13):** 4 vértices (`WantVertex`, `CanVertex`, `MustVertex`, `KnowVertex`, todos `a wcmkf:CoreVertex`), 5 `AggregationPolicy`, 4 `DomainProfile`. As "24 facetas" são **classes**, não indivíduos — e simultaneamente sujeitas de `hasAggregationPolicy`/`isCriticalInDomain` e alvos de shapes (`rdf:type hasValue owl:Class`): uso híbrido classe/indivíduo.

---

## E — Lacunas (o que falta formalizar)

**(i) Compartilhamento de facetas entre pilares com pesos distintos.** Não há `contributesToVertex`, `secondaryVertex` nem `facetWeightInVertex`. Fix mínimo: relaxar `sh:maxCount 1` para `sh:maxCount 4` + `sh:in (WantVertex, CanVertex, MustVertex, KnowVertex)`; remover o `AllDisjointClasses` (ou introduzir `FacetRole` com `hasWeight` por papel); criar `wcmkf:FacetContribution` (faceta, vértice, β, θ) como classe — hoje não existe nenhuma classe capaz de携带 um par (faceta, pilar, peso).

**(ii) Agregação formal.** A política é apenas uma *etiqueta* (`aggregationMode` string + `allowsCompensation` boolean). Não existe: fórmula, ordem de aplicação, prioridade entre overrides, agregação por pilar (não há `wantScore`/`canScore`/`mustScore`/`knowScore` na ontologia de facetas — só em `wcmk-assessment.ttl`, desconectada), κ(c,a) de materialidade contextual, recalculo de risco residual. O único cálculo do corpus é `deficitValue = max(0, required − observed)` (tolerância 1e-6). Sem β (0 instâncias no TTL; 0.80 uniforme no exemplo) e sem θ, as 5 políticas são nominalmente declaradas mas **inoperacionais**.

**(iii) Metacognição/aprendibilidade.** `UncertaintyAwareness` é uma classe-faceta sem estrutura meta: `hasConfidence` é opcional, não há distribuição de incerteza (só decimal escalar), não há `hasConfidenceInterval`, `validUntil`, `reassessmentOf`, `supersedes`, `learningRate` nem versionamento de avaliação. `CalibrationArtifact` tem **zero propriedades e zero indivíduos** — o loop "run de calibração → ajuste de θ → reavaliação" não é representável. Não há trace de evolução temporal (`prov:qualifiedAssertion`, `dcterms:modified`).

**(iv) Legitimidade de intenção.** `GoalOrientation` e `IntentionalStability` não carregam finalidade declarada nem cadeia de justificação: ausentes `hasStatedGoal`, `hasOperationalTarget`, `alignedWithValue`, `violatesValue`, `mandate/authority`, `consent`, `justificationFor`. `requiresHumanReview` existe fora da ontologia de facetas; nenhuma shape impõe review quando M1/M4 caem abaixo de 0.20 (as duas únicas guards emitem apenas `sh:Warning`, não bloqueio).

**Veredicto:** o núcleo taxonômico (24 facetas, 37 classes, 24 políticas ligadas, deficit aritmeticamente coerente) está sólido e SHACL-conforme; o modelo é **descritivo, não operacional**: β, θ, agregação multi-pilar, metacognição e legitimidade permanecem prose do catálogo, não ontologia. Prioridade de correção: (1) `FacetContribution` com β/θ por vértice e domínio; (2) `DomainProfileShape` com θ obrigatórios e 6 perfis faltantes; (3) `FacetizedAgencyProfileShape` ligando `hasFacet`↔`hasAssessment` e removendo a ambiguidade de severidade; (4) `CalibrationArtifact` tipificado com versão e data.
