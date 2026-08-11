"""enterprise multi-tenant platform

Revision ID: 0003
Revises: 0002
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    statements = """
    CREATE TABLE organizations (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name varchar(180) UNIQUE NOT NULL,
      slug varchar(100) UNIQUE NOT NULL, is_active boolean NOT NULL DEFAULT true,
      settings jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz DEFAULT now());
    INSERT INTO organizations(name,slug) VALUES ('TicketSense Demo Enterprise','ticketsense-demo');
    ALTER TABLE users ADD COLUMN tenant_id uuid REFERENCES organizations(id);
    ALTER TABLE departments ADD COLUMN tenant_id uuid REFERENCES organizations(id);
    ALTER TABLE tickets ADD COLUMN tenant_id uuid REFERENCES organizations(id);
    ALTER TABLE knowledge_base ADD COLUMN tenant_id uuid REFERENCES organizations(id);
    UPDATE users SET tenant_id=(SELECT id FROM organizations LIMIT 1);
    UPDATE departments SET tenant_id=(SELECT id FROM organizations LIMIT 1);
    UPDATE tickets SET tenant_id=(SELECT id FROM organizations LIMIT 1);
    UPDATE knowledge_base SET tenant_id=(SELECT id FROM organizations LIMIT 1);
    CREATE INDEX ix_users_tenant_id ON users(tenant_id); CREATE INDEX ix_tickets_tenant_id ON tickets(tenant_id);
    CREATE INDEX ix_departments_tenant_id ON departments(tenant_id); CREATE INDEX ix_knowledge_base_tenant_id ON knowledge_base(tenant_id);
    ALTER TABLE users DROP CONSTRAINT ck_users_role;
    ALTER TABLE users ADD CONSTRAINT ck_users_role CHECK (role IN ('customer','support_agent','manager','enterprise_admin','ai_admin','knowledge_manager','security_admin','end_user','department_engineer','admin'));
    CREATE TABLE audit_logs (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL REFERENCES organizations(id), user_id uuid REFERENCES users(id), action varchar(100) NOT NULL, resource_type varchar(80) NOT NULL, resource_id varchar(100), metadata_json jsonb DEFAULT '{}', ip_address varchar(64), created_at timestamptz DEFAULT now());
    CREATE INDEX ix_audit_logs_tenant_id ON audit_logs(tenant_id); CREATE INDEX ix_audit_logs_action ON audit_logs(action);
    CREATE TABLE notifications (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL REFERENCES organizations(id), user_id uuid NOT NULL REFERENCES users(id), title varchar(180) NOT NULL, message text NOT NULL, kind varchar(40) DEFAULT 'info', is_read boolean DEFAULT false, created_at timestamptz DEFAULT now());
    CREATE INDEX ix_notifications_tenant_id ON notifications(tenant_id); CREATE INDEX ix_notifications_user_id ON notifications(user_id);
    CREATE TABLE incidents (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL REFERENCES organizations(id), title varchar(255) NOT NULL, service varchar(160) NOT NULL, status varchar(30) DEFAULT 'investigating', severity varchar(20) DEFAULT 'high', ticket_count integer DEFAULT 0, growth_rate numeric DEFAULT 0, common_symptom text, created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now());
    CREATE INDEX ix_incidents_tenant_id ON incidents(tenant_id);
    CREATE TABLE knowledge_articles (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL REFERENCES organizations(id), department_id uuid REFERENCES departments(id), title varchar(255) NOT NULL, body text NOT NULL, status varchar(30) DEFAULT 'draft', version varchar(20) DEFAULT '1.0', source_ticket_ids jsonb DEFAULT '[]', approved_by uuid REFERENCES users(id), created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now());
    CREATE INDEX ix_knowledge_articles_tenant_id ON knowledge_articles(tenant_id);
    CREATE TABLE sla_policies (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL REFERENCES organizations(id), name varchar(160) NOT NULL, priority varchar(20) NOT NULL, response_minutes integer NOT NULL, resolution_minutes integer NOT NULL, is_active boolean DEFAULT true, created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now());
    CREATE INDEX ix_sla_policies_tenant_id ON sla_policies(tenant_id);
    CREATE TABLE integrations (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL REFERENCES organizations(id), provider varchar(60) NOT NULL, name varchar(120) NOT NULL, enabled boolean DEFAULT false, config jsonb DEFAULT '{}', created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now());
    CREATE INDEX ix_integrations_tenant_id ON integrations(tenant_id);
    CREATE TABLE ai_decisions (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), tenant_id uuid NOT NULL REFERENCES organizations(id), ticket_id uuid NOT NULL REFERENCES tickets(id) ON DELETE CASCADE, agent_name varchar(100) NOT NULL, decision jsonb NOT NULL, confidence numeric, latency_ms integer, success boolean DEFAULT true, created_at timestamptz DEFAULT now());
    CREATE INDEX ix_ai_decisions_tenant_id ON ai_decisions(tenant_id); CREATE INDEX ix_ai_decisions_ticket_id ON ai_decisions(ticket_id); CREATE INDEX ix_ai_decisions_agent_name ON ai_decisions(agent_name);
    """
    # asyncpg rejects multiple SQL commands in one prepared statement. Alembic runs
    # the migration transactionally, so execute each DDL/DML statement separately.
    for statement in statements.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_decisions, integrations, sla_policies, knowledge_articles, incidents, notifications, audit_logs CASCADE")
    op.drop_column("knowledge_base", "tenant_id"); op.drop_column("tickets", "tenant_id"); op.drop_column("departments", "tenant_id"); op.drop_column("users", "tenant_id")
    op.drop_table("organizations")
