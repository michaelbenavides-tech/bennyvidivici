from app.models import FrameworkMapping

PHASES: list[dict] = [
    {
        "key": "01_requirements",
        "name": "Requirements & Risk Definition",
        "description": "Define risk tier, obligations, oversight, data sensitivity, threat scope, and acceptance criteria.",
        "artifacts": ["policy_document", "threat_model"],
        "items": [
            ("risk_tier_defined", "Risk tier classification documented", ["NIST AI RMF:GOVERN", "MAESTRO:L2"]),
            ("regulatory_scope", "Regulatory obligations mapped", ["NIST AI RMF:GOVERN"]),
            ("human_oversight", "Human oversight requirements defined", ["OWASP Agent:A-06", "OWASP LLM:LLM08"]),
            ("data_sensitivity", "Data sensitivity classification documented", ["OWASP LLM:LLM06", "GDPR:Art. 5"]),
            ("threat_model_scope", "MAESTRO layers applicable to this system agreed", ["MAESTRO:All"]),
            ("test_acceptance", "Security test acceptance criteria defined", ["SP 800-218A:PW.8"]),
            ("oss_model_policy", "OSS model assessment policy defined", ["OWASP LLM:LLM05", "ATLAS:TA0013"]),
            ("api_disclosure_policy", "API metadata disclosure policy defined", ["ATLAS:TA0001"]),
            ("capability_allowlist", "Minimum capability allowlist documented", ["OWASP LLM:LLM08", "OWASP Agent:A-02"]),
        ],
    },
    {
        "key": "02_design",
        "name": "Design & Architecture Security",
        "description": "Design guardrails, trust hierarchy, permissions, identity, and isolation.",
        "artifacts": ["architecture_diagram", "threat_model"],
        "items": [
            ("guardrail_architecture", "4-layer guardrail architecture designed", ["OWASP LLM:LLM01", "OWASP LLM:LLM02", "OWASP LLM:LLM06", "OWASP LLM:LLM08"]),
            ("trust_hierarchy", "Agent trust hierarchy documented", ["OWASP Agent:A-04", "MAESTRO:L6"]),
            ("permission_tier_model", "T0-T3 action permission model designed", ["OWASP LLM:LLM08", "OWASP Agent:A-02"]),
            ("maestro_threat_model", "MAESTRO 7-layer threat model completed", ["MAESTRO:All"]),
            ("mcp_gateway_design", "MCP security gateway architecture designed", ["MAESTRO:L5", "OWASP LLM:LLM07"]),
            ("identity_design", "Agent IAM specification completed", ["MAESTRO:L2", "OWASP Agent:A-10"]),
            ("network_segmentation", "Network isolation architecture defined", ["MAESTRO:L1", "ATLAS:TA0004"]),
        ],
    },
    {
        "key": "03_data_governance",
        "name": "Data Governance & Training Data Security",
        "description": "Govern provenance, privacy, anomaly detection, data SBOM, erasure, and training access.",
        "artifacts": ["policy_document", "sbom"],
        "items": [
            ("data_provenance_policy", "Data provenance standards documented", ["SP 800-218A:PW.3.1", "SP 800-218A:PW.3.2"]),
            ("pii_scrubbing", "PII scanning process defined", ["OWASP LLM:LLM06", "GDPR:Art. 17"]),
            ("anomaly_detection", "Training data anomaly detection process defined", ["SP 800-218A:PW.3.1", "OWASP LLM:LLM03"]),
            ("data_sbom", "Data SBOM format and process defined", ["SP 800-218A:PS.3.2"]),
            ("erasure_workflow", "Right-to-erasure workflow documented", ["GDPR:Art. 17", "OWASP LLM:LLM06"]),
            ("pipeline_access_control", "Training pipeline access controls documented", ["ATLAS:TA0013", "SP 800-218A:PW.3"]),
            ("adversarial_samples", "Adversarial sample inclusion policy defined", ["SP 800-218A:PW.3.3"]),
        ],
    },
    {
        "key": "04_model_development",
        "name": "Model Development Security",
        "description": "Secure OSS model selection, registry, SBOM, training isolation, and backdoor testing.",
        "artifacts": ["sbom", "test_report"],
        "items": [
            ("oss_gates_completed", "All OSS model assessment gates passed", ["OWASP LLM:LLM05", "ATLAS:TA0006"]),
            ("private_registry", "Private model registry configured", ["SP 800-218A:PS.1.1"]),
            ("model_sbom", "Model SBOM generated", ["SP 800-218A:PS.3.2"]),
            ("reward_model_separate", "Reward model stored separately", ["SP 800-218A:PS.1.1"]),
            ("training_isolation", "Training environment isolated", ["MAESTRO:L1", "SP 800-218A:PO.5"]),
            ("backdoor_testing", "Behavioral consistency testing completed", ["ATLAS:TA0006", "OWASP LLM:LLM03"]),
        ],
    },
    {
        "key": "05_integration",
        "name": "Integration, Build & DevSecOps",
        "description": "Secure tools, schemas, identities, prompts, dependencies, and pipeline gates.",
        "artifacts": ["architecture_diagram", "policy_document"],
        "items": [
            ("tool_definition_review", "MCP tool definitions reviewed for poisoning", ["MAESTRO:L5", "OWASP LLM:LLM07", "OWASP Agent:A-03"]),
            ("schema_validation", "Tool parameter schema validation implemented", ["OWASP LLM:LLM02", "OWASP LLM:LLM07"]),
            ("sequence_detection", "Dangerous tool combination detection implemented", ["MAESTRO:L5", "ATLAS:TA0011"]),
            ("service_identities", "Separate service identity per tool type configured", ["MAESTRO:L2", "OWASP LLM:LLM08"]),
            ("pipeline_gates", "AI-extended DevSecOps pipeline gates implemented", ["SP 800-218A:PW.4.4"]),
            ("prompt_static_analysis", "Prompt template static analysis integrated", ["OWASP LLM:LLM01"]),
            ("dependency_pinning", "ML dependencies pinned to verified versions", ["ATLAS:TA0013", "SP 800-218A:PW.4.4"]),
        ],
    },
    {
        "key": "06_security_testing",
        "name": "Security Testing & Red Teaming",
        "description": "Run injection, agency, leakage, supply chain, memory, tool, DoS, and red-team testing.",
        "artifacts": ["red_team_report", "test_report"],
        "items": [
            ("injection_battery", "Prompt injection battery completed", ["OWASP LLM:LLM01", "OWASP Agent:A-01", "ATLAS:AML.T0051"]),
            ("agency_testing", "Agency and permission tests completed", ["OWASP LLM:LLM08", "OWASP Agent:A-02"]),
            ("pii_leakage_testing", "PII leakage test suite passed", ["OWASP LLM:LLM06"]),
            ("supply_chain_validation", "Model artifact integrity verified", ["OWASP LLM:LLM05", "ATLAS:TA0013"]),
            ("a2a_trust_testing", "Multi-agent trust boundary tests completed", ["OWASP Agent:A-04", "MAESTRO:L6"]),
            ("memory_poisoning_test", "RAG memory poisoning tests completed", ["OWASP Agent:A-05", "MAESTRO:L3"]),
            ("mcp_tool_poisoning_test", "Tool poisoning tests completed", ["OWASP LLM:LLM07", "MAESTRO:L5"]),
            ("dos_testing", "Resource exhaustion and DoS tests completed", ["OWASP LLM:LLM04", "OWASP LLM:LLM10"]),
            ("red_team_report", "Red team report generated", ["SP 800-218A:PW.8"]),
        ],
    },
    {
        "key": "07_deployment",
        "name": "Secure Deployment & Runtime Controls",
        "description": "Activate guardrails, credentials, segmentation, observability, incident response, and limits.",
        "artifacts": ["policy_document", "architecture_diagram"],
        "items": [
            ("guardrails_active", "All guardrail layers active in production", ["OWASP LLM:LLM01", "OWASP LLM:LLM02", "OWASP LLM:LLM06", "OWASP LLM:LLM08"]),
            ("imdsv2_enforced", "IMDSv2 enforced on AI infrastructure", ["MAESTRO:L1"]),
            ("jit_credentials", "JIT task-scoped credentials configured", ["MAESTRO:L2", "OWASP Agent:A-10"]),
            ("network_segmentation_verified", "Agent network isolation verified", ["MAESTRO:L1", "ATLAS:TA0004"]),
            ("observability_active", "Reasoning traces and anomaly detection active", ["OWASP Agent:A-09", "MAESTRO:All"]),
            ("ir_playbooks_tested", "AI incident response playbooks tested", ["NIST AI RMF:MANAGE"]),
            ("rate_limits_live", "Rate limits and blast radius controls active", ["OWASP LLM:LLM04", "OWASP LLM:LLM10"]),
        ],
    },
    {
        "key": "08_monitoring",
        "name": "Monitoring, Detection & Incident Response",
        "description": "Operate baselines, traces, anomaly rules, classifier metrics, IR playbooks, and red-team cadence.",
        "artifacts": ["test_report", "policy_document"],
        "items": [
            ("kri_baseline", "Behavioral baseline and KRI thresholds established", ["NIST AI RMF:MEASURE", "OWASP Agent:A-09"]),
            ("trace_capture", "Reasoning trace capture operational", ["OWASP Agent:A-09"]),
            ("anomaly_detection_active", "Automated anomaly detection rules live", ["ATLAS:TA0009", "MAESTRO:All"]),
            ("classifier_monitoring", "Guardrail classifier false negative rate tracked", ["NIST AI RMF:MEASURE"]),
            ("ir_playbooks_documented", "AI-specific IR playbooks documented and tested", ["NIST AI RMF:MANAGE"]),
            ("monthly_red_team", "Monthly red team schedule established", ["SP 800-218A:PW.8"]),
        ],
    },
    {
        "key": "09_retirement",
        "name": "Model Retirement & Data Disposal",
        "description": "Dispose of model weights, datasets, vector stores, caches, and credentials.",
        "artifacts": ["policy_document"],
        "items": [
            ("weights_deleted", "Model weights deleted from all storage locations", ["OWASP LLM:LLM06", "ATLAS:TA0011"]),
            ("datasets_archived", "Training datasets archived per retention policy", ["GLBA:Retention", "MAESTRO:L3"]),
            ("vector_store_purged", "Vector store embeddings deleted", ["OWASP Agent:A-05", "GDPR:Art. 17"]),
            ("inference_cache_cleared", "Inference caches and KV caches cleared", ["OWASP LLM:LLM06"]),
            ("credentials_revoked", "All agent credentials and API keys revoked", ["MAESTRO:L2"]),
        ],
    },
]


FRAMEWORK_REFERENCES = {
    "OWASP LLM": [f"LLM{i:02d}" for i in range(1, 11)],
    "OWASP Agent": [f"A-{i:02d}" for i in range(1, 11)],
    "MAESTRO": [f"L{i}" for i in range(1, 8)],
    "ATLAS": [f"TA{i:04d}" for i in range(1, 15)],
    "NIST AI RMF": ["GOVERN", "MAP", "MEASURE", "MANAGE"],
    "SP 800-218A": ["PW.1.1", "PW.3", "PW.3.1", "PW.3.2", "PW.3.3", "PW.4.4", "PW.8", "PS.1", "PS.3.2"],
}


def parse_refs(refs: list[str]) -> list[dict[str, str]]:
    parsed = []
    for ref in refs:
        framework, reference_id = ref.split(":", 1)
        parsed.append({"framework": framework, "id": reference_id, "name": reference_id})
    return parsed


def seed_frameworks(db) -> None:
    if db.query(FrameworkMapping).count():
        return
    rows = []
    for phase in PHASES:
        for item in phase["items"]:
            for ref in parse_refs(item[2]):
                rows.append(
                    FrameworkMapping(
                        phase_key=phase["key"],
                        framework=ref["framework"],
                        reference_id=ref["id"],
                        reference_name=ref["name"],
                        description=f"{ref['framework']} {ref['id']} mapped by {item[1]}",
                        severity="high" if phase["key"] in {"01_requirements", "06_security_testing"} else "medium",
                        control_type="control",
                    )
                )
    for framework, refs in FRAMEWORK_REFERENCES.items():
        for ref in refs:
            rows.append(
                FrameworkMapping(
                    phase_key="reference",
                    framework=framework,
                    reference_id=ref,
                    reference_name=ref,
                    description=f"{framework} reference {ref}",
                    severity="medium",
                    control_type="control",
                )
            )
    db.add_all(rows)
    db.commit()
