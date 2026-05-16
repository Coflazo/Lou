#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "demo-data" / "generated-contract-pdfs"


CONTRACTS = [
    {
        "slug": "enterprise-saas-subscription",
        "title": "Enterprise SaaS Subscription Agreement",
        "party_a": "Siemens Digital Industries Software GmbH",
        "party_b": "Northwind Analytics Ltd.",
        "effective_date": "1 June 2026",
        "law": "laws of Germany",
        "venue": "courts of Munich, Germany",
        "subject": "cloud-based analytics, dashboarding, and workflow automation services",
        "deliverables": "production tenant, administrator console, audit log exports, uptime reporting, onboarding workshops, and migration support",
        "regulated_data": "customer usage data, uploaded operational records, administrator credentials, telemetry, and support tickets",
        "risk_focus": "service levels, data ownership, renewal controls, and suspension rights",
    },
    {
        "slug": "mutual-non-disclosure",
        "title": "Mutual Non-Disclosure Agreement",
        "party_a": "Siemens Legal Operations",
        "party_b": "Aster Robotics SAS",
        "effective_date": "3 June 2026",
        "law": "laws of France",
        "venue": "courts of Paris, France",
        "subject": "evaluation of a possible robotics supply and integration relationship",
        "deliverables": "technical demonstrations, architecture workshops, diligence materials, security questionnaires, and commercial proposals",
        "regulated_data": "confidential business plans, technical drawings, source-adjacent materials, pricing models, and prototype performance data",
        "risk_focus": "residual knowledge, compelled disclosure, return of materials, and non-use covenants",
    },
    {
        "slug": "data-processing-addendum",
        "title": "Data Processing Addendum",
        "party_a": "Siemens Smart Infrastructure AG",
        "party_b": "Harbor Cloud Processing Inc.",
        "effective_date": "5 June 2026",
        "law": "laws of Ireland",
        "venue": "courts of Dublin, Ireland",
        "subject": "processing of personal data in connection with hosted building-management services",
        "deliverables": "processor commitments, subprocessor notices, transfer assessments, breach support, and deletion certificates",
        "regulated_data": "tenant contact details, device identifiers, access logs, building telemetry linked to persons, and support metadata",
        "risk_focus": "GDPR Article 28 duties, international transfers, subprocessor approvals, and breach notice timing",
    },
    {
        "slug": "ai-vendor-evaluation",
        "title": "AI Vendor Evaluation and Deployment Agreement",
        "party_a": "Siemens Advanta Consulting",
        "party_b": "LumenForge AI BV",
        "effective_date": "8 June 2026",
        "law": "laws of the Netherlands",
        "venue": "courts of Amsterdam, Netherlands",
        "subject": "evaluation and controlled deployment of generative AI tools for legal intake and contract triage",
        "deliverables": "sandbox access, prompt templates, evaluation reports, model cards, admin telemetry, and deployment recommendations",
        "regulated_data": "prompts, uploaded contract excerpts, reviewer feedback, model outputs, and red-team findings",
        "risk_focus": "training restrictions, output ownership, explainability, auditability, and human oversight",
    },
    {
        "slug": "professional-services",
        "title": "Professional Services Agreement",
        "party_a": "Siemens Energy Global GmbH",
        "party_b": "Delta Program Management LLP",
        "effective_date": "10 June 2026",
        "law": "laws of England and Wales",
        "venue": "courts of London, England",
        "subject": "program management, process design, and implementation support for energy infrastructure projects",
        "deliverables": "project plans, status dashboards, governance packs, workshop outputs, risk registers, and final transition materials",
        "regulated_data": "project budgets, engineering milestones, supplier names, plant schedules, and privileged strategy notes",
        "risk_focus": "scope control, acceptance criteria, personnel continuity, and change-order discipline",
    },
    {
        "slug": "software-license-maintenance",
        "title": "Software License and Maintenance Agreement",
        "party_a": "Siemens Mobility GmbH",
        "party_b": "VectorSignal Systems AB",
        "effective_date": "12 June 2026",
        "law": "laws of Sweden",
        "venue": "courts of Stockholm, Sweden",
        "subject": "licensing and support of embedded diagnostic software for rail-signaling environments",
        "deliverables": "licensed binaries, documentation, maintenance releases, defect corrections, security patches, and escrow deposit materials",
        "regulated_data": "license keys, diagnostic logs, configuration files, vulnerability reports, and railway operation metadata",
        "risk_focus": "source code escrow, audit rights, export control, support response times, and license scope",
    },
    {
        "slug": "master-procurement",
        "title": "Master Procurement and Supply Agreement",
        "party_a": "Siemens Healthineers AG",
        "party_b": "Orchid Precision Components Sp. z o.o.",
        "effective_date": "15 June 2026",
        "law": "laws of Poland",
        "venue": "courts of Warsaw, Poland",
        "subject": "supply of precision mechanical components used in medical imaging equipment",
        "deliverables": "qualified components, inspection reports, certificates of conformity, spare parts, and corrective action plans",
        "regulated_data": "product specifications, batch records, supplier audits, quality investigations, and regulated manufacturing files",
        "risk_focus": "quality controls, recall support, warranty remedies, delivery commitments, and regulatory cooperation",
    },
    {
        "slug": "reseller-channel",
        "title": "Reseller and Channel Partner Agreement",
        "party_a": "Siemens Industry Software Inc.",
        "party_b": "Metroline Digital Solutions LLC",
        "effective_date": "18 June 2026",
        "law": "laws of New York",
        "venue": "state and federal courts located in New York County, New York",
        "subject": "authorized resale and implementation support for industrial software subscriptions",
        "deliverables": "qualified opportunities, reseller quotes, customer onboarding coordination, sales reports, and compliance certifications",
        "regulated_data": "customer lead data, discount approvals, deal-registration records, end-user information, and channel performance metrics",
        "risk_focus": "territory limits, anti-bribery controls, discount leakage, customer ownership, and termination transition",
    },
    {
        "slug": "cloud-security-addendum",
        "title": "Cloud Security Addendum",
        "party_a": "Siemens Cybersecurity Services",
        "party_b": "BeaconEdge Hosting Oy",
        "effective_date": "20 June 2026",
        "law": "laws of Finland",
        "venue": "courts of Helsinki, Finland",
        "subject": "security requirements for managed cloud hosting and infrastructure operations",
        "deliverables": "security control matrix, penetration-test summaries, incident runbooks, vulnerability remediation plans, and compliance evidence",
        "regulated_data": "security logs, privileged account records, vulnerability scans, encryption keys metadata, and incident evidence",
        "risk_focus": "incident response, audit access, encryption controls, logging retention, and subcontractor governance",
    },
    {
        "slug": "public-sector-framework",
        "title": "Public Sector Framework Agreement",
        "party_a": "Siemens Public Sector Solutions GmbH",
        "party_b": "CivicGrid Procurement Authority",
        "effective_date": "24 June 2026",
        "law": "laws of Belgium",
        "venue": "courts of Brussels, Belgium",
        "subject": "framework supply of digital infrastructure, maintenance, and integration services for public-sector buyers",
        "deliverables": "call-off procedures, service catalogs, pricing schedules, reporting packs, accessibility statements, and compliance certificates",
        "regulated_data": "public procurement records, citizen-service metadata, call-off orders, audit trails, and regulatory correspondence",
        "risk_focus": "public audit rights, transparency obligations, budget termination, accessibility, and anti-corruption compliance",
    },
]


ARTICLE_TITLES = [
    "Definitions and Interpretation",
    "Scope of Work and Ordering Mechanics",
    "Delivery, Acceptance, and Operational Governance",
    "Fees, Taxes, Invoicing, and Records",
    "Confidentiality, Publicity, and Residual Knowledge",
    "Data Protection, Security, and Regulated Information",
    "Intellectual Property, Licenses, and Work Product",
    "Compliance, Audit, and Subcontracting",
    "Warranties, Indemnities, Liability, and Insurance",
    "Term, Termination, Transition, and Dispute Resolution",
]


def escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def clause_block(contract: dict[str, str], article_number: int, title: str) -> str:
    subject = escape(contract["subject"])
    deliverables = escape(contract["deliverables"])
    regulated_data = escape(contract["regulated_data"])
    risk_focus = escape(contract["risk_focus"])
    party_a = escape(contract["party_a"])
    party_b = escape(contract["party_b"])

    return rf"""
\section*{{Article {article_number}. {title}}}
\addcontentsline{{toc}}{{section}}{{Article {article_number}. {title}}}
\noindent\textbf{{Commercial purpose.}} The parties enter this Article to allocate responsibility for {subject}. The obligations below are intended to be operationally testable and not merely aspirational. Each party shall maintain records sufficient to show compliance, and neither party may treat silence in an order form, statement of work, or schedule as permission to reduce the protections stated in this Agreement.

\medskip
\noindent\textbf{{Core obligations.}} {party_b} shall provide, manage, and document {deliverables}. {party_a} shall provide timely decisions, access to reasonably necessary stakeholders, and accurate instructions. Where a dependency is not satisfied, the affected party shall give written notice identifying the dependency, the consequence for timing or cost, and the mitigation steps available without expanding the original scope.

\medskip
\noindent\textbf{{Control language.}} Any ambiguity in this Article shall be resolved in favor of preserving {risk_focus}. A waiver must be express, written, and signed by an authorized representative. A course of dealing, delayed objection, acceptance of partial performance, or payment of an invoice does not waive future enforcement or modify the standard of care.

\begin{{enumerate}}[label=\alph*.]
\item The parties shall maintain a decision log for matters that affect {risk_focus}. The log must identify the requester, approver, date, evidence reviewed, residual risk, and any follow-up obligation.
\item Records involving {regulated_data} must be segregated from general project material, retained only for the approved retention period, and made available for audit where the Agreement grants audit rights.
\item Personnel performing material obligations must be qualified for the role assigned. Replacement personnel must receive transition briefings and may not reduce continuity for critical services, milestones, or regulated deliverables.
\item Each party shall notify the other promptly after discovering facts that could reasonably affect performance, security, compliance, financial exposure, or the enforceability of this Agreement.
\end{{enumerate}}

\noindent\textbf{{Escalation and remedy.}} If a dispute arises under this Article, the parties shall first escalate to project leads, then to legal and commercial executives. The parties shall continue undisputed performance while the dispute is pending. Equitable relief remains available for confidentiality, data protection, intellectual property, security, and non-use obligations.
"""


def render_contract(contract: dict[str, str]) -> str:
    article_pages = "\n\\clearpage\n".join(
        clause_block(contract, index, title) for index, title in enumerate(ARTICLE_TITLES, start=1)
    )
    return rf"""
\documentclass[11pt]{{article}}
\usepackage[a4paper,margin=1in]{{geometry}}
\usepackage{{array}}
\usepackage{{enumitem}}
\usepackage{{fancyhdr}}
\usepackage{{hyperref}}
\usepackage{{microtype}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{8pt}}
\pagestyle{{fancy}}
\fancyhf{{}}
\lhead{{{escape(contract["title"])}}}
\rhead{{Lou Demo Contract}}
\cfoot{{\thepage}}
\begin{{document}}
\begin{{titlepage}}
\centering
\vspace*{{1.2in}}
{{\LARGE\bfseries {escape(contract["title"])}}}\par
\vspace{{0.4in}}
{{\large Full Text Demonstration Agreement}}\par
\vspace{{0.8in}}
\begin{{tabular}}{{>{{\bfseries}}p{{1.7in}}p{{4.4in}}}}
Party A & {escape(contract["party_a"])}\\
Party B & {escape(contract["party_b"])}\\
Effective Date & {escape(contract["effective_date"])}\\
Governing Law & {escape(contract["law"])}\\
Venue & {escape(contract["venue"])}\\
Primary Subject & {escape(contract["subject"])}\\
Risk Focus & {escape(contract["risk_focus"])}\\
\end{{tabular}}
\vfill
\textit{{Generated for Lou contract-review demos. This document is synthetic and should not be used as legal advice.}}
\end{{titlepage}}
\tableofcontents
\clearpage
{article_pages}
\clearpage
\section*{{Signature Blocks}}
\addcontentsline{{toc}}{{section}}{{Signature Blocks}}
\begin{{tabular}}{{p{{2.8in}}p{{2.8in}}}}
\textbf{{{escape(contract["party_a"])}}} & \textbf{{{escape(contract["party_b"])}}}\\[0.7in]
By: \hrulefill & By: \hrulefill\\[0.2in]
Name: \hrulefill & Name: \hrulefill\\[0.2in]
Title: \hrulefill & Title: \hrulefill\\[0.2in]
Date: \hrulefill & Date: \hrulefill\\
\end{{tabular}}
\end{{document}}
"""


def compile_pdf(tex_path: Path, output_dir: Path) -> None:
    command = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={output_dir}",
        str(tex_path),
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    for suffix in (".aux", ".log", ".out", ".toc"):
        artifact = output_dir / f"{tex_path.stem}{suffix}"
        if artifact.exists():
            artifact.unlink()


def main() -> None:
    if shutil.which("pdflatex") is None:
        raise SystemExit("pdflatex is required to generate contract PDFs.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_pdf in OUTPUT_DIR.glob("*.pdf"):
        old_pdf.unlink()

    with tempfile.TemporaryDirectory(prefix="lou-contract-build-") as temp:
        temp_dir = Path(temp)
        for index, contract in enumerate(CONTRACTS, start=1):
            tex_path = temp_dir / f"{index:02d}-{contract['slug']}.tex"
            tex_path.write_text(render_contract(contract), encoding="utf-8")
            compile_pdf(tex_path, OUTPUT_DIR)

    print(f"Generated {len(CONTRACTS)} contract PDFs in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
