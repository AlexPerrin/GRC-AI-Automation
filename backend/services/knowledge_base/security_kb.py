"""
Security Controls Knowledge Base entries.
Maps control domains (NIST CSF, SOC 2 TSC, ISO 27001) to requirement descriptions.
Seeded into ChromaDB collection 'kb_security' on first startup.
"""

SECURITY_KB_ENTRIES: list[dict] = [
    {
        "id": "ac_nist_pr_ac",
        "text": (
            "NIST CSF PR.AC — Identity Management and Access Control. Access to physical and "
            "logical assets and associated facilities is limited to authorised users, processes, "
            "and devices, and is managed consistent with the assessed risk of unauthorised access "
            "to authorised activities and transactions. Key practices include: managing identities "
            "and credentials for authorised devices, users, and processes; managing access "
            "permissions and authorisations; managing remote access; managing access for "
            "third-party stakeholders; implementing least privilege; and protecting the integrity "
            "of the identity and access management infrastructure. Multi-factor authentication "
            "must be implemented for all privileged accounts and remote access connections."
        ),
        "metadata": {"framework": "NIST CSF", "domain": "Access Control", "control_id": "PR.AC"},
    },
    {
        "id": "ac_soc2_cc6",
        "text": (
            "SOC 2 CC6 — Logical and Physical Access Controls. The entity implements logical "
            "access security software, infrastructure, and architectures over protected "
            "information assets to protect them from security events. CC6.1 requires the entity "
            "to implement logical access security measures to protect against threats from "
            "sources outside its system boundaries. CC6.2 requires prior to issuing system "
            "credentials and granting system access, the entity registers and authorises new "
            "internal and external users. CC6.3 requires the entity authorises, modifies, or "
            "removes access to data, software, functions, and other protected information assets "
            "based on approved and documented access requests and changes aligned with role-based "
            "access principles. CC6.6 requires the entity implements logical access security "
            "measures to protect against threats from sources outside its system boundaries "
            "including filtering of network traffic."
        ),
        "metadata": {"framework": "SOC 2", "domain": "Access Control", "control_id": "CC6"},
    },
    {
        "id": "dp_nist_pr_ds",
        "text": (
            "NIST CSF PR.DS — Data Security. Information and records (data) are managed "
            "consistent with the organisation's risk strategy to protect the confidentiality, "
            "integrity, and availability of information. Key practices include: data-at-rest "
            "is protected; data-in-transit is protected; assets are formally managed throughout "
            "removal, transfers, and disposition; adequate capacity to ensure availability is "
            "maintained; protections against data leaks are implemented; integrity checking "
            "mechanisms are used to verify software, firmware, and information integrity; and "
            "the development and testing environments are separate from the production "
            "environment. Encryption standards must be documented and applied consistently "
            "based on data classification levels."
        ),
        "metadata": {"framework": "NIST CSF", "domain": "Data Protection", "control_id": "PR.DS"},
    },
    {
        "id": "dp_iso27001_a8",
        "text": (
            "ISO 27001 Annex A.8 — Asset Management. A.8.1 requires that assets associated with "
            "information and information processing facilities are identified and an inventory of "
            "these assets is drawn up and maintained. Rules for the acceptable use of information "
            "and assets must be identified, documented, and implemented. All assets must be "
            "returned upon termination of employment or contract. A.8.2 requires information to "
            "be classified in terms of legal requirements, value, criticality, and sensitivity to "
            "unauthorised disclosure or modification. Information must be labelled and handled in "
            "accordance with the classification scheme. A.8.3 requires that procedures for "
            "managing removable media are implemented in accordance with the classification "
            "scheme; media shall be disposed of securely when no longer required using formal "
            "procedures."
        ),
        "metadata": {"framework": "ISO 27001", "domain": "Data Protection", "control_id": "A.8"},
    },
    {
        "id": "ir_nist_rs_rp",
        "text": (
            "NIST CSF RS.RP — Response Planning. Response processes and procedures are executed "
            "and maintained to ensure timely response to detected cybersecurity events. A response "
            "plan must be executed during or after an incident. The plan must include: roles and "
            "responsibilities for response activities; communication plans for internal and "
            "external stakeholders; criteria for activating the incident response process; "
            "escalation procedures; evidence preservation and forensic analysis capabilities; "
            "eradication and recovery procedures; and post-incident review processes. The "
            "response plan must be tested at least annually through tabletop exercises or "
            "simulations to verify effectiveness and identify gaps."
        ),
        "metadata": {"framework": "NIST CSF", "domain": "Incident Response", "control_id": "RS.RP"},
    },
    {
        "id": "ir_soc2_cc7",
        "text": (
            "SOC 2 CC7 — System Operations. The entity monitors system components and the "
            "operation of those controls including the detection of anomalies, investigation of "
            "anomalies, and resolution of identified security incidents. CC7.3 requires the "
            "entity to evaluate security events to determine whether they could or have resulted "
            "in a failure of the entity to meet its objectives (security incidents) and, if so, "
            "takes actions to prevent or address such failures. CC7.4 requires the entity to "
            "respond to identified security incidents by executing a defined incident response "
            "program to understand, contain, remediate, and communicate security incidents as "
            "appropriate. CC7.5 requires the entity to identify, develop, and implement "
            "activities to recover from identified security incidents and restore operations to "
            "normal as quickly as possible."
        ),
        "metadata": {"framework": "SOC 2", "domain": "Incident Response", "control_id": "CC7"},
    },
    {
        "id": "vm_nist_id_ra",
        "text": (
            "NIST CSF ID.RA — Risk Assessment. The organisation understands the cybersecurity "
            "risk to organisational operations (including mission, functions, image, or "
            "reputation), organisational assets, and individuals. Asset vulnerabilities are "
            "identified and documented. Information is received from information sharing forums "
            "and sources about threats and vulnerabilities. Threats, vulnerabilities, likelihoods, "
            "and impacts are used to determine risk. Threats, vulnerabilities, likelihoods, and "
            "impacts are used to determine risk. Risk responses are identified and prioritised. "
            "A vulnerability management programme must include regular scanning using an "
            "authenticated scanner, remediation prioritised by CVSS score, and patch application "
            "timelines (critical ≤ 30 days, high ≤ 60 days, medium ≤ 90 days)."
        ),
        "metadata": {
            "framework": "NIST CSF",
            "domain": "Vulnerability Management",
            "control_id": "ID.RA",
        },
    },
    {
        "id": "vm_soc2_cc7_1",
        "text": (
            "SOC 2 CC7.1 — Vulnerability Management. To meet its objectives, the entity uses "
            "detection and monitoring procedures to identify changes to configurations or new "
            "vulnerabilities. The entity monitors system components and the operation of those "
            "controls. Procedures include: use of intrusion detection systems; monitoring of "
            "vulnerability alerts from vendors, government agencies, and information sharing "
            "groups; performance of periodic vulnerability scans; and remediation of "
            "vulnerabilities in a timely manner based on the risk they present. The entity "
            "evaluates security events to determine whether they could or have resulted in a "
            "failure to meet objectives. Penetration testing must be conducted at least annually "
            "by qualified third parties to validate the effectiveness of security controls."
        ),
        "metadata": {
            "framework": "SOC 2",
            "domain": "Vulnerability Management",
            "control_id": "CC7.1",
        },
    },
    {
        "id": "bc_soc2_a1",
        "text": (
            "SOC 2 Availability Criteria A1 — Business Continuity. The entity maintains, "
            "monitors, and evaluates current processing capacity and use of system components "
            "(infrastructure, data, and software) to manage capacity demand and enable the "
            "implementation of additional capacity to help meet its objectives. A1.2 requires "
            "the entity to authorise, design, develop or acquire, implement, operate, approve, "
            "maintain, and monitor environmental protections, software, data back-up processes, "
            "and recovery infrastructure to meet its availability commitments and system "
            "requirements. Business continuity and disaster recovery plans must be documented, "
            "tested at least annually, and updated based on test results. Recovery Time Objective "
            "(RTO) and Recovery Point Objective (RPO) must be defined and validated."
        ),
        "metadata": {
            "framework": "SOC 2",
            "domain": "Business Continuity",
            "control_id": "A1",
        },
    },
    {
        "id": "bc_iso27001_a17",
        "text": (
            "ISO 27001 Annex A.17 — Information Security Aspects of Business Continuity "
            "Management. A.17.1 requires that the organisation determine its requirements for "
            "information security and the continuity of information security management in adverse "
            "situations. Business continuity plans should address information security requirements "
            "and must be documented and tested. A.17.1.2 requires that the organisation establish, "
            "document, implement, and maintain processes, procedures, and controls to ensure the "
            "required level of continuity for information security during an adverse situation. "
            "A.17.1.3 requires that the organisation verify the established and implemented "
            "information security continuity controls at regular intervals to ensure they are "
            "valid and effective during adverse situations. A.17.2 requires that information "
            "processing facilities are implemented with sufficient redundancy."
        ),
        "metadata": {
            "framework": "ISO 27001",
            "domain": "Business Continuity",
            "control_id": "A.17",
        },
    },
    {
        "id": "sc_nist_id_sc",
        "text": (
            "NIST CSF ID.SC — Supply Chain Risk Management. The organisation's priorities, "
            "constraints, risk tolerances, and assumptions are established and used to support "
            "risk decisions associated with managing supply chain risk. The organisation has "
            "established and implemented the processes to identify, assess, and manage supply "
            "chain risks. Suppliers and third-party partners of information systems, components, "
            "and services are identified, prioritised, and assessed using a supply chain risk "
            "assessment process. Suppliers and third-party partners are routinely assessed using "
            "audits, test results, or other forms of evaluations to confirm they are meeting "
            "their contractual obligations. Response and recovery planning and testing are "
            "conducted with suppliers and third-party providers. Contracts with suppliers must "
            "include security requirements, audit rights, and incident notification obligations."
        ),
        "metadata": {
            "framework": "NIST CSF",
            "domain": "Supply Chain",
            "control_id": "ID.SC",
        },
    },
    {
        "id": "sc_soc2_cc9",
        "text": (
            "SOC 2 CC9 — Risk Mitigation including Vendor and Business Partner Risk. CC9.2 "
            "requires the entity to assess and manages risks associated with vendors and business "
            "partners. The entity identifies vendors and business partners that present risks to "
            "the entity and implements risk mitigation strategies. Due diligence is performed "
            "prior to entering into relationships with vendors and business partners including "
            "assessment of financial stability, security practices, and operational capability. "
            "Ongoing monitoring of vendor performance against commitments and service level "
            "agreements is performed. Contracts include provisions for data handling, "
            "confidentiality, security requirements, audit rights, and termination procedures. "
            "Subprocessor relationships of vendors must also be evaluated and managed to ensure "
            "adequate controls exist throughout the supply chain."
        ),
        "metadata": {
            "framework": "SOC 2",
            "domain": "Supply Chain",
            "control_id": "CC9",
        },
    },
]
