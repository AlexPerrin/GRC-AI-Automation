"""
Legal / Regulatory Knowledge Base entries.
Each entry maps a regulatory requirement to a structured description.
Seeded into ChromaDB collection 'kb_legal' on first startup.
"""

LEGAL_KB_ENTRIES: list[dict] = [
    {
        "id": "gdpr_art5",
        "text": (
            "GDPR Article 5 establishes the core principles for processing personal data. "
            "Data must be processed lawfully, fairly, and transparently. It must be collected "
            "for specified, explicit, and legitimate purposes and not further processed in a "
            "manner incompatible with those purposes. Data shall be adequate, relevant, and "
            "limited to what is necessary (data minimisation). It must be accurate and kept up "
            "to date. Data must not be kept longer than necessary (storage limitation). "
            "Processing must ensure appropriate security including protection against unauthorised "
            "or unlawful processing and against accidental loss, destruction or damage (integrity "
            "and confidentiality). The controller is responsible for and must demonstrate "
            "compliance with these principles (accountability)."
        ),
        "metadata": {"regulation": "GDPR", "jurisdiction": "EU", "article": "Art. 5"},
    },
    {
        "id": "gdpr_art28",
        "text": (
            "GDPR Article 28 governs the relationship between data controllers and data processors. "
            "Controllers must only use processors that provide sufficient guarantees to implement "
            "appropriate technical and organisational measures so that processing will meet GDPR "
            "requirements and ensure the protection of the rights of the data subject. Processing "
            "by a processor shall be governed by a binding contract or legal act. The processor "
            "shall process personal data only on documented instructions from the controller. "
            "The processor must ensure persons authorised to process data are committed to "
            "confidentiality. The processor must assist the controller in ensuring compliance "
            "with security obligations, data breach notification, DPIAs, and prior consultation. "
            "The processor must delete or return all personal data after the end of services."
        ),
        "metadata": {"regulation": "GDPR", "jurisdiction": "EU", "article": "Art. 28"},
    },
    {
        "id": "gdpr_art32",
        "text": (
            "GDPR Article 32 requires controllers and processors to implement appropriate technical "
            "and organisational measures to ensure a level of security appropriate to the risk. "
            "Measures include: pseudonymisation and encryption of personal data; the ability to "
            "ensure ongoing confidentiality, integrity, availability and resilience of processing "
            "systems; the ability to restore availability and access to personal data in a timely "
            "manner in the event of a physical or technical incident; and a process for regularly "
            "testing, assessing and evaluating the effectiveness of security measures. In assessing "
            "the appropriate level of security, account shall be taken of the risks presented by "
            "processing, in particular accidental or unlawful destruction, loss, alteration, "
            "unauthorised disclosure of, or access to personal data."
        ),
        "metadata": {"regulation": "GDPR", "jurisdiction": "EU", "article": "Art. 32"},
    },
    {
        "id": "pipeda_4_1",
        "text": (
            "PIPEDA Principle 4.1 — Accountability. An organisation is responsible for personal "
            "information under its control and shall designate an individual or individuals who are "
            "accountable for the organisation's compliance with the following principles. "
            "Accountability for the organisation's compliance with the principles rests with the "
            "designated individual(s), even though other individuals within the organisation may "
            "be responsible for the day-to-day collection and processing of personal information. "
            "Other individuals within the organisation may be delegated to act on behalf of the "
            "designated individual(s). Organisations shall implement policies and practices to "
            "give effect to the principles, including training staff and communicating information "
            "about the organisation's policies and practices."
        ),
        "metadata": {"regulation": "PIPEDA", "jurisdiction": "Canada", "article": "Principle 4.1"},
    },
    {
        "id": "pipeda_4_7",
        "text": (
            "PIPEDA Principle 4.7 — Safeguards. Personal information shall be protected by "
            "security safeguards appropriate to the sensitivity of the information. The safeguards "
            "shall protect personal information against loss or theft, as well as unauthorised "
            "access, disclosure, copying, use, or modification. Organisations shall protect "
            "personal information regardless of the format in which it is held. The nature of the "
            "safeguards will vary with the sensitivity of the information, the amount accumulated, "
            "the distribution of the information, and the format of the information. More sensitive "
            "information should be safeguarded by a higher level of protection. Methods of "
            "protection should include: physical measures (locked filing cabinets); organisational "
            "measures (security clearances and limiting access on a need-to-know basis); and "
            "technological measures (passwords and encryption)."
        ),
        "metadata": {"regulation": "PIPEDA", "jurisdiction": "Canada", "article": "Principle 4.7"},
    },
    {
        "id": "pipeda_4_9",
        "text": (
            "PIPEDA Principle 4.9 — Individual Access. Upon request, an individual shall be "
            "informed of the existence, use, and disclosure of his or her personal information "
            "and shall be given access to that information. An individual shall be able to "
            "challenge the accuracy and completeness of the information and have it amended as "
            "appropriate. An organisation shall respond to an individual's request within a "
            "reasonable time and at minimal or no cost. The requested information shall be "
            "provided in a form that is generally understandable. When requested, the organisation "
            "shall explain the source of the personal information and provide a list of any "
            "organisations to which it has disclosed the personal information."
        ),
        "metadata": {"regulation": "PIPEDA", "jurisdiction": "Canada", "article": "Principle 4.9"},
    },
    {
        "id": "cppa_s12",
        "text": (
            "Canada's Consumer Privacy Protection Act (CPPA) Section 12 — Purposes. An "
            "organisation may collect, use or disclose personal information only for purposes "
            "that a reasonable person would consider appropriate in the circumstances. Before or "
            "at the time of collection, the organisation must identify the purposes for which "
            "personal information is collected. An organisation may not collect personal "
            "information indiscriminately. The purposes must be described in a manner that the "
            "individual can reasonably understand. Where the information is to be used for a "
            "purpose not previously identified, the new purpose must be identified before use "
            "and additional consent must be obtained."
        ),
        "metadata": {"regulation": "CPPA", "jurisdiction": "Canada", "article": "s.12"},
    },
    {
        "id": "cppa_s57",
        "text": (
            "Canada's Consumer Privacy Protection Act (CPPA) Section 57 — Security Safeguards. "
            "An organisation must protect personal information by implementing security "
            "safeguards appropriate to the sensitivity of the information. Safeguards must "
            "protect the information against risks such as unauthorised access, collection, use, "
            "disclosure, copying, modification, disposal, or destruction. The organisation must "
            "ensure that service providers that process personal information on its behalf "
            "implement comparable safeguards. When an organisation no longer requires personal "
            "information, it must destroy the information or render it non-identifiable in a "
            "secure manner."
        ),
        "metadata": {"regulation": "CPPA", "jurisdiction": "Canada", "article": "s.57"},
    },
    {
        "id": "hipaa_164_308",
        "text": (
            "HIPAA Security Rule § 164.308 — Administrative Safeguards. Covered entities and "
            "business associates must implement administrative actions, policies, and procedures "
            "to manage the selection, development, implementation, and maintenance of security "
            "measures to protect electronic protected health information (ePHI). Required "
            "implementation specifications include: security management process (risk analysis "
            "and risk management); assigned security responsibility (designate security official); "
            "workforce security (authorisation, supervision, termination procedures); information "
            "access management; security awareness and training; security incident procedures "
            "(identify and respond to suspected security incidents); contingency plan (data backup, "
            "disaster recovery, emergency mode operations); and evaluation (periodic technical "
            "and non-technical evaluation of security policies and procedures)."
        ),
        "metadata": {"regulation": "HIPAA", "jurisdiction": "USA", "article": "§ 164.308"},
    },
    {
        "id": "hipaa_164_312",
        "text": (
            "HIPAA Security Rule § 164.312 — Technical Safeguards. Covered entities and business "
            "associates must implement technical security measures to guard against unauthorised "
            "access to ePHI transmitted over an electronic communications network. Required "
            "implementation specifications include: access control (unique user identification, "
            "emergency access procedure, automatic logoff, encryption and decryption); audit "
            "controls (hardware, software, and procedural mechanisms to record and examine "
            "access and activity in information systems); integrity controls (mechanisms to "
            "authenticate ePHI and ensure it has not been altered or destroyed in an "
            "unauthorised manner); and transmission security (encryption of ePHI in transit)."
        ),
        "metadata": {"regulation": "HIPAA", "jurisdiction": "USA", "article": "§ 164.312"},
    },
    {
        "id": "pci_dss_req3",
        "text": (
            "PCI DSS Requirement 3 — Protect Stored Account Data. Cardholder data storage must "
            "be kept to a minimum. Storage policies must limit the data amount and retention time "
            "to that which is required for legal, regulatory, and business requirements. Primary "
            "account numbers (PAN) must be rendered unreadable wherever stored using strong "
            "cryptography (e.g., AES-256), one-way hashes, truncation, or tokenisation. "
            "Sensitive authentication data (SAD) must not be stored after authorisation even if "
            "encrypted. Cryptographic keys used to encrypt cardholder data must be protected "
            "against disclosure and misuse with strict key management procedures including key "
            "generation, distribution, storage, retirement, and destruction."
        ),
        "metadata": {"regulation": "PCI DSS", "jurisdiction": "Global", "article": "Req. 3"},
    },
    {
        "id": "pci_dss_req6",
        "text": (
            "PCI DSS Requirement 6 — Develop and Maintain Secure Systems and Software. All "
            "system components must be protected from known vulnerabilities by installing "
            "applicable security patches. Critical patches must be installed within one month "
            "of release. A process must be in place to identify newly discovered security "
            "vulnerabilities. Software development processes must follow industry standards for "
            "secure coding, including addressing common vulnerabilities such as injection flaws, "
            "broken authentication, sensitive data exposure, security misconfiguration, and "
            "cross-site scripting. Web-facing applications must be reviewed for vulnerabilities "
            "via code review or web application firewall (WAF). Change control procedures must "
            "document impact, management sign-off, and testing before implementation."
        ),
        "metadata": {"regulation": "PCI DSS", "jurisdiction": "Global", "article": "Req. 6"},
    },
    {
        "id": "pci_dss_req12",
        "text": (
            "PCI DSS Requirement 12 — Support Information Security with Organisational Policies "
            "and Programs. An information security policy must be established, published, "
            "maintained, and disseminated to all personnel. The policy must address all PCI DSS "
            "requirements and include an annual review process. A risk assessment process must "
            "be implemented that identifies threats and vulnerabilities, resulting in a formal "
            "risk assessment. Usage policies for critical technologies (remote access, wireless, "
            "removable media, laptops, PDAs, email, internet) must be defined. An incident "
            "response plan must be in place to respond immediately to a system breach. Service "
            "provider relationships must be managed with a list of service providers, written "
            "agreements acknowledging shared responsibility, and a program for engaging them."
        ),
        "metadata": {"regulation": "PCI DSS", "jurisdiction": "Global", "article": "Req. 12"},
    },
    {
        "id": "gdpr_art13",
        "text": (
            "GDPR Article 13 — Information to be Provided where Personal Data are Collected from "
            "the Data Subject. Where personal data relating to a data subject are collected from "
            "the data subject, the controller shall, at the time when personal data are obtained, "
            "provide the data subject with the identity and contact details of the controller and "
            "data protection officer; the purposes and legal basis for processing; the legitimate "
            "interests pursued (where applicable); recipients or categories of recipients; "
            "international transfer safeguards; retention period; the existence of rights to "
            "access, rectification, erasure, restriction, portability, and objection; the right "
            "to withdraw consent at any time; the right to lodge a complaint with a supervisory "
            "authority; and whether provision of data is a statutory or contractual requirement."
        ),
        "metadata": {"regulation": "GDPR", "jurisdiction": "EU", "article": "Art. 13"},
    },
    {
        "id": "gdpr_art35",
        "text": (
            "GDPR Article 35 — Data Protection Impact Assessment (DPIA). Where a type of "
            "processing is likely to result in a high risk to the rights and freedoms of natural "
            "persons, the controller shall carry out an assessment of the impact of the envisaged "
            "processing operations on the protection of personal data. A DPIA is required in "
            "particular where: systematic and extensive profiling with significant effects occurs; "
            "large-scale processing of special categories of data occurs; or systematic monitoring "
            "of a publicly accessible area occurs. The DPIA must contain a systematic description "
            "of processing operations and purposes, an assessment of necessity and proportionality, "
            "an assessment of risks to data subjects, and measures to address the risks. Results "
            "must be taken into account when performing processing."
        ),
        "metadata": {"regulation": "GDPR", "jurisdiction": "EU", "article": "Art. 35"},
    },
]
