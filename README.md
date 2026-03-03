<h1 align="center">AI Vendor Onboarding Orchestrator</h1>

<p align="center">
  <b>Governance, Risk, and Compliance Workflow for humans and AI agents.</b><br/>
  Automates legal, security, and financial risk analysis — so analysts spend time deciding, not researching.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/frontend-React%20%C2%B7%20TypeScript-informational" />
  <img src="https://img.shields.io/badge/backend-Python%20%C2%B7%20FastAPI%20%C2%B7%20LangChain%20%C2%B7%20ChromaDB%20%C2%B7%20LiteLLM-informational" />
</p>

Vendor onboarding in security-conscious organizations is slow by design because it has to be. Analysts manually review legal agreements, security questionnaires, and financial disclosures, then synthesize findings across multiple regulatory frameworks such as PIPEDA, GDPR, CPPA, SOC 2, and PCI DSS. They coordinate across Product, Legal, Security, and Finance before a decision can be made. Shared context between reviewers is limited, findings are rarely cited to specific clauses, and decisions are difficult to audit retroactively. In many organizations, this process takes weeks.

This system compresses that timeline to hours without removing human judgment from the process.

An analyst uploads vendor documentation, and the pipeline automatically runs four parallel due diligence stages. Each AI powered stage uses retrieval-augmented generation (RAG) to ground its analysis in both the vendor’s submitted materials and an internal knowledge base of compliance frameworks. The analyst receives structured findings with per-criterion assessments, explicit evidence citations from the vendor’s own documents, identified control gaps, and a recommended risk posture.

The analyst can now review a complete, cited, multi framework risk assessment in under an hour across legal, security, and financial domains without reading raw documents end to end. The role shifts from researcher to decision maker.

What AI is responsible for includes ingesting and parsing vendor documentation, chunking and embedding content into a vector store, retrieving relevant passages against targeted compliance queries, cross-referencing vendor claims against regulatory requirements and internal control frameworks, generating structured findings with citations, and maintaining an audit trail of analysis steps and workflow decisions.

Where AI must stop is at the final approval decision and at accountability. The decision to APPROVE, APPROVE WITH CONDITIONS, or REJECT remains exclusively with a human analyst. Risk acceptance carries regulatory, financial, and operational consequences that flow to real audit findings and liability. Accountability cannot be delegated to a model. A human signature represents ownership of the decision and its downstream impact. Preserving that boundary maintains scrutiny over AI generated analysis and ensures incentives remain aligned with responsible risk management.

What breaks first at scale is enterprise readiness. As adoption expands, security and governance requirements for handling sensitive vendor documentation become primary constraints. The system must support SSO integration, role based access control, detailed logging, and defensible audit trails aligned to enterprise standards. Data residency and encryption controls must be clearly defined.

Retrieval quality is the second major pressure point. As the internal knowledge base grows and document volume increases, embedding quality and query relevance determine overall system accuracy. Improving real-world performance requires iterative refinement of the RAG pipeline, expansion and curation of the knowledge base, and investment in hybrid retrieval that combines dense and sparse methods. Cross-encoder re-ranking can further improve precision. Model versioning must be pinned in the audit log to prevent rubric drift as underlying models evolve.

## Demo

https://github.com/user-attachments/assets/6d34ec3c-8131-4b9a-a957-9a08b88ff141

[YouTube Mirror](https://www.youtube.com/watch?v=wHG9BitjcRM)

## whoami

**Hands-on AI experience:** 2-3 years. 

At KOHO Financial, I built and shipped an LLM-powered vendor security due diligence pipeline (The security review portion of this project) that reduced review turnaround from months to under a week. I was inspired by this experience to create a multi-agent workflow to assist with the entire vendor onboarding workflow end-to-end.

I have a degree in Software Engineering, where I studied machine learning and artificial intelligence.<br>[CMPE 452: Neural and Genetic Computing](https://github.com/AlexPerrin/School-Assignments/tree/1fd6403c9ffe2b7e6607f66dd1cd26b69bc15c63/CMPE%20452%3A%20Neural%20and%20Genetic%20Computing)

I've also explored personal projects in machine learning, such as a security intrusion detection system to classify malicious network traffic. [Machine Learning Plugin for Snort3 Intrusion Detection System](https://github.com/AlexPerrin/snort3_ml)

## Quickstart

```bash
git clone git@github.com:AlexPerrin/GRC-AI-Automation.git
cd GRC-AI-Automation
```

Open `.env` and set `LLM_PROVIDER_API_KEY` to your Anthropic, OpenAI, or OpenRouter API key.<br>
The `LLM_PROVIDER` and `LLM_MODEL` variables have working defaults (`anthropic` / `claude-sonnet-4-6`).

```
docker compose up --build
```

**The app is running at [`http://localhost:5173`](http://localhost:5173)**

Optionally, seed three pre-built vendor scenarios (clean pass, legal rejection, conditional approval) to explore the full workflow without uploading real documents:

```bash
curl -X POST http://localhost:8000/dev/seed
```

## Documentation

[Wiki → Problem Definition](../../wiki/Problem-Definition)

[Wiki → Project Plan](../../wiki/Project-Plan)

[Wiki → Technical Specification](../../wiki/Technical-Specification)

<p align="center">Copyright © 2026 <a href="https://github.com/AlexPerrin">Alex Perrin</a> · <a href="https://github.com/AlexPerrin/GRC-AI-Automation/blob/main/LICENSE">MIT License</a></p>
