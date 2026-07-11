## Complex Document for RAG Parsing Tests

Synthetic  15-page  PDF  with  paragraphs,  simple  and  complex  tables,  diagrams,  scanned-form  style  image,  metadata examples, and production RAG edge cases.

## Story Line

Three client teams - Arka Finance, BlueLeaf Retail, and CityRide Mobility - are migrating contracts, policies, support records, and  operational  reports  into  a  single  RAG  platform.  Each  team  has  different  document  types,  access  rules,  and  parsing challenges. The RAG system must answer questions with citations while ensuring that one client never sees another clients data.

This  PDF  is  intentionally  designed  to  test  document  loaders,  PDF  parsers,  OCR  workflows,  table  extraction,  chunking strategies, metadata preservation, and source citation quality.

Key statement: RAG does not train the model. RAG gives the model the right context before answering.

| Section               | Parsing challenge                                  | Why it matters for RAG                  |
|-----------------------|----------------------------------------------------|-----------------------------------------|
| Contracts             | Dense legal text, clause numbers, cross references | Need section-aware chunks and citations |
| Tables                | Merged headers, numeric columns, footnotes         | Need row/column preservation            |
| Images                | Architecture diagram, heatmap, scanned form        | Need OCR or multimodal extraction       |
| Multi-tenant metadata | client_id, document_id, contract_group_id          | Need access-safe retrieval              |

## 1. Business Scenario

The platform team is building a document intelligence layer for contract operations. Legal users need answers such as: Which contracts  renew  automatically?  Which  agreements  have  a  60-day  termination  notice?  Which  documents  mention  data residency in India? These questions require retrieval across multiple document types and sometimes across multiple related documents of a single client.

Support teams also want answers from SOPs, markdown runbooks, HTML exports, chat transcripts, and CSV logs. A single parser is not enough because the corpus contains born-digital PDFs, scanned forms, HTML, markdown, and spreadsheet-like tables.

| Client            | Main document family             | Risk   | Primary users        | Typical question                            |
|-------------------|----------------------------------|--------|----------------------|---------------------------------------------|
| Arka Finance      | MSA, audit addendum, DPA         | High   | Legal and compliance | What audit rights exist in the DPA?         |
| BlueLeaf Retail   | MSA, pricing, support SLA        | Medium | Procurement          | Which clause controls renewal pricing?      |
| CityRide Mobility | Ops reports, incident logs, SOPs | Medium | Operations           | Which depot had repeated battery incidents? |

<!-- image -->

Caption: Ownership map showing how client admins, legal teams, audit teams, document storage, vector storage, and the RAG service interact.

## 2. Raw Data Inventory

The ingestion team receives files from multiple sources. Some files are clean and digital; others contain scanned pages, rotated tables, missing metadata, embedded images, or formula-generated values. The inventory below intentionally includes different formats and extraction expectations.

| Asset ID       | Client            | Format      | Pages/Rows   | Expected extraction          | Notes                                    |
|----------------|-------------------|-------------|--------------|------------------------------|------------------------------------------|
| ARK-MSA-001    | Arka Finance      | PDF         | 32 pages     | Clauses, tables, signatures  | Born-digital text with footer references |
| ARK-DPA-002    | Arka Finance      | DOCX        | 18 pages     | Headings, lists, tables      | Track changes removed before ingestion   |
| BLR-PRICE-00 3 | BlueLeaf Retail   | XLSX        | 12 sheets    | Rate cards, discounts        | Merged cells and formulas                |
| BLR-SLA-004    | BlueLeaf Retail   | PDF         | 9 pages      | SLA table, escalation matrix | Table crosses page boundary              |
| CRM-OPS-005    | CityRide Mobility | CSV         | 48,200 rows  | Incident records             | Needs column type normalization          |
| CRM-FORM-00 6  | CityRide Mobility | Scanned PDF | 4 pages      | OCR fields, checkbox         | Low contrast and slight rotation         |
| KB-RUN-007     | Shared            | Markdown    | 14 files     | Runbook sections             | Good for heading-based chunks            |
| WEB-FAQ-008    | Shared            | HTML        | 23 pages     | FAQ content, links           | Needs boilerplate removal                |

Parsing difficulty increases when a document combines multiple layouts: paragraph text, tables, images, and notes. Good parsers preserve structure; weak parsers flatten everything into a noisy text stream.

## 3. Contract Excerpt: Dense Legal Text

Clause 7.2  -  Confidential  Information.  The  Receiving  Party  shall  protect  Confidential  Information  using  at  least  the  same degree of care that it uses to protect its own confidential materials, but in no event less than reasonable care. Confidential Information includes technical documents, pricing schedules, user lists, API keys, operational procedures, security reports, incident response notes, product roadmaps, and any derived analysis prepared by the Receiving Party.

Clause  7.3  -  Exclusions.  Confidential  Information  does  not  include  information  that  is  publicly  available  without  breach, independently developed without reference to the Disclosing Party material, received lawfully from a third party, or approved for release in writing. The burden of proving an exclusion remains with the Receiving Party.

Clause 9.1  -  Data  Residency.  If  the  Statement  of  Work  identifies  a  specific  processing  region,  the  service  provider  shall process production records only within that region unless the client approves a transfer in writing. Disaster recovery replicas may be stored in a secondary region if encryption at rest and access logging are enabled.

Clause 11.4 - Termination Assistance. Upon termination, the provider shall make client data available for export for a period of thirty days. After the export period, the provider may delete production data according to the deletion schedule unless a legal hold applies.

|   Clause | Short name             | Owner            | Trigger                          | Required action                                                           | Citation hint       |
|----------|------------------------|------------------|----------------------------------|---------------------------------------------------------------------------|---------------------|
|      7.2 | Confidentiality        | Receiving Party  | Receipt of confidential material | Protect information with reasonable care and equivalent internal controls | Page 4, clause 7.2  |
|      9.1 | Data residency         | Service Provider | SOW specifies region             | Process production records only in approved region                        | Page 4, clause 9.1  |
|     11.4 | Termination assistance | Service Provider | Agreement termination            | Provide export window for 30 days                                         | Page 4, clause 11.4 |

Parser note: clause numbering is important. Chunking should not remove or split clause identifiers because users often ask questions using clause numbers.

## 4. Simple Table: Policy Rules

The following table is intentionally simple. It should be correctly extracted by most PDF table parsers. It tests basic row and column detection, short text values, and numeric values.

| Policy Area       | Rule                                                          | Owner            | Review Cycle        |
|-------------------|---------------------------------------------------------------|------------------|---------------------|
| Refunds           | Refund requests must be raised within 7 days of purchase.     | Customer Support | Quarterly           |
| Data Export       | Client admins can request export in CSV or JSON format.       | Platform Ops     | Monthly             |
| Access Review     | Privileged access must be reviewed every 30 days.             | Security         | Monthly             |
| Incident Response | Critical incidents require acknowledgement within 30 minutes. | SRE              | After each incident |
| Vendor Review     | High-risk vendors require annual risk assessment.             | Procurement      | Annual              |

## Narrative Around the Table

This  table  appears  between  paragraphs,  which  is  common  in  enterprise  documents.  A  good  parser  should  preserve  the paragraph before the table, the table content, and the paragraph after the table in the correct reading order.

For RAG systems, simple tables are often converted into row-wise text chunks such as: Policy Area: Refunds; Rule: Refund requests must be raised within 7 days; Owner: Customer Support.

## 5. Complex Table: SLA, Escalation, and Credits

This table uses long cells and operational footnotes. It is designed to test whether the parser can retain header hierarchy and map values to the correct columns.

| Service Category   | Severity                  | Response Target   | Resolution Target   | Service Credit                | Evidence Required                            |
|--------------------|---------------------------|-------------------|---------------------|-------------------------------|----------------------------------------------|
| API Availability   | P1 - complete outage      | 15 minutes        | 4 hours             | 10 percent monthly fee credit | Monitoring logs and incident ticket          |
| API Availability   | P2 - degraded performance | 30 minutes        | 8 hours             | 5 percent monthly fee credit  | Latency dashboard and affected endpoint list |
| Data Pipeline      | P1 - ingestion stopped    | 20 minutes        | 6 hours             | 8 percent pipeline fee credit | Queue depth, failed job IDs, replay report   |
| Data Pipeline      | P3 - delayed batch        | 4 hours           | Next business day   | No automatic credit           | Batch ID and SLA exception note              |
| Support            | P2 - urgent support       | 1 hour            | 1 business day      | 2 percent support fee credit  | Support ticket with timestamps               |

Footnote A: Service credits are not cumulative across the same service category for the same calendar month. Footnote B: Credits do not apply when delay is caused by client-side network restrictions, missing credentials, or force majeure events.

Parser note: table footnotes should remain attached to the table. If the footnote is separated, an answer about credits may become incomplete or misleading.

## 6. Image: RAG Architecture Diagram

The diagram below represents the ingestion and retrieval flow. Some PDF parsers ignore images completely, while others extract image metadata but not the text inside the image. For production use, image content may require OCR or multimodal extraction.

<!-- image -->

Caption: A simplified RAG pipeline showing raw files, parsing, chunking, embeddings, vector database, retriever, LLM, and grounded answer generation.

| Image element   | Potential extraction method          | Expected output                      |
|-----------------|--------------------------------------|--------------------------------------|
| Box labels      | OCR or vision model Layout or vision | Raw Files, Parser, Chunks, Vector DB |
| Arrows          | understanding                        | Processing order                     |
| Caption         | Normal PDF text extraction           | Description of the diagram           |

## 7. Markdown Runbook Excerpt

Markdown  files  are  often  easier  to  parse  because  headings  and  code  blocks  are  explicit.  However,  when  markdown  is exported to PDF, the structure may become visual rather than semantic.

```
# Runbook: Contract Ingestion Failure ## Symptoms - Upload status remains `processing` for more than 30 minutes. - Worker logs show repeated timeout errors. - Vector count does not increase for the affected document. ## Recovery Steps 1. Confirm the object exists in document storage. 2. Re-run parser with `safe_mode=True`. 3. Rebuild chunks with the previous chunking configuration. 4. Compare chunk count with the last successful ingestion. 5. Trigger re-embedding only for changed chunks.
```

A good parser should preserve code block boundaries and avoid mixing numbered steps with surrounding prose. In RAG, runbooks are useful because users often ask operational questions that require exact steps.

| Runbook field   | Value                      | Parsing expectation                     |
|-----------------|----------------------------|-----------------------------------------|
| Title           | Contract Ingestion Failure | Should become section title metadata    |
| Symptoms        | Five bullet items          | Should remain as list or separate lines |
| Recovery Steps  | Numbered sequence          | Order must be preserved                 |

## 8. Scanned Form and OCR Challenge

This page contains a scanned-form style image. Text inside the form is not normal selectable PDF text. A simple text parser may miss it entirely. OCR-based systems should extract labels, values, and checkboxes from the image.

<!-- image -->

Caption: The form includes fields such as Client Name, Contract ID, Effective Date, Renewal Type, Data Region, Reviewer, and a checkbox approval statement.

| Field             | Expected OCR value      | Validation rule                               |
|-------------------|-------------------------|-----------------------------------------------|
| Client Name       | BlueLeaf Retail Pvt Ltd | Must match known client list                  |
| Contract ID       | BLR-MSA-2026-019        | Pattern: client-code + type + year + sequence |
| Effective Date    | 01 Apr 2026             | Date parser should normalize to ISO format    |
| Approval checkbox | Checked                 | Boolean extraction required                   |

## 9. Multiple Documents for One Client

BlueLeaf  Retail  has  five  related  contract  documents.  If  these  documents  are  indexed  independently  without  relationship metadata,  the  retriever  may  miss  cross-document  context.  The  platform  uses  a  contract\_group\_id  to  connect  related documents.

| document_id   | document_type            | contract_group_id   | effective_date   | relationship                       |
|---------------|--------------------------|---------------------|------------------|------------------------------------|
| BLR-MSA-001   | Master Service Agreement | BLR-ACME-2026       | 2026-04-01       | Base commercial agreement          |
| BLR-NDA-002   | NDA                      | BLR-ACME-2026       | 2026-04-01       | Confidentiality terms              |
| BLR-SOW-003   | Statement of Work        | BLR-ACME-2026       | 2026-04-15       | Project scope and deliverables     |
| BLR-PRICE-004 | Pricing Amendment        | BLR-ACME-2026       | 2026-05-01       | Updated pricing and discount tiers |
| BLR-SLA-005   | Support SLA              | BLR-ACME-2026       | 2026-05-10       | Support response and credits       |

Example  question:  What  does  the  BlueLeaf  agreement  say  about  termination  assistance  and  pricing  changes?  A  good retriever may need chunks from the MSA and the Pricing Amendment together.

Relationship metadata allows retrieval across related documents without mixing unrelated client data.