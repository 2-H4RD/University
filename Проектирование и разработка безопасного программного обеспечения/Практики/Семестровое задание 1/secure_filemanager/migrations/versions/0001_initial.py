"""Initial schema, append-only audit and guarded database function."""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE SCHEMA fm;
    REVOKE ALL ON SCHEMA fm FROM PUBLIC;
    CREATE TABLE fm.users (
      id UUID PRIMARY KEY,
      username VARCHAR(32) NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
      active BOOLEAN NOT NULL DEFAULT TRUE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
    );
    CREATE TABLE fm.files (
      id UUID PRIMARY KEY,
      owner_id UUID NOT NULL REFERENCES fm.users(id) ON DELETE RESTRICT,
      name VARCHAR(255) NOT NULL,
      name_key VARCHAR(255) NOT NULL,
      storage_key VARCHAR(32) NOT NULL,
      size BIGINT NOT NULL CHECK (size >= 0),
      sha256 CHAR(64) NOT NULL,
      format TEXT NOT NULL CHECK (format IN ('text','binary','json','xml','zip')),
      version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
      deleted BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
    );
    CREATE UNIQUE INDEX uq_live_name ON fm.files(owner_id,name_key) WHERE NOT deleted;
    CREATE INDEX ix_files_owner ON fm.files(owner_id);
    CREATE TABLE fm.audit_head (
      singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
      seq BIGINT NOT NULL DEFAULT 0,
      signature CHAR(64) NOT NULL
    );
    INSERT INTO fm.audit_head VALUES (TRUE, 0, repeat('0',64));
    CREATE TABLE fm.operations (
      id BIGINT PRIMARY KEY,
      occurred_at TIMESTAMPTZ NOT NULL,
      user_id UUID REFERENCES fm.users(id) ON DELETE RESTRICT,
      file_id UUID REFERENCES fm.files(id) ON DELETE RESTRICT,
      action VARCHAR(32) NOT NULL,
      outcome TEXT NOT NULL CHECK (outcome IN ('success','failure')),
      reason VARCHAR(64) NOT NULL,
      request_id UUID NOT NULL,
      payload JSONB NOT NULL,
      previous_hmac CHAR(64) NOT NULL,
      hmac CHAR(64) NOT NULL
    );
    CREATE INDEX ix_operations_user_time ON fm.operations(user_id,occurred_at);
    CREATE INDEX ix_operations_file ON fm.operations(file_id);
    CREATE TABLE fm.storage_jobs (
      id UUID PRIMARY KEY,
      keys JSONB NOT NULL,
      state TEXT NOT NULL CHECK (state IN ('pending','done','recovered')),
      created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
    );
    CREATE TABLE fm.auth_attempts (
      name_key CHAR(64) PRIMARY KEY,
      attempts INTEGER NOT NULL CHECK (attempts >= 0),
      window_started TIMESTAMPTZ NOT NULL,
      blocked_until TIMESTAMPTZ
    );
    CREATE FUNCTION fm.append_event(p_seq BIGINT, p_data JSONB, p_prev TEXT, p_sig TEXT)
    RETURNS VOID LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = pg_catalog, fm, pg_temp AS $$
    DECLARE last_seq BIGINT; last_sig TEXT;
    BEGIN
      SELECT seq, signature INTO last_seq, last_sig FROM fm.audit_head
        WHERE singleton = TRUE FOR UPDATE;
      IF p_seq <> last_seq + 1 OR p_prev <> last_sig OR
         p_data->>'seq' <> p_seq::text OR p_data->>'previous_hmac' <> p_prev OR
         p_sig !~ '^[a-f0-9]{64}$' THEN
        RAISE EXCEPTION 'invalid audit sequence';
      END IF;
      INSERT INTO fm.operations
       (id,occurred_at,user_id,file_id,action,outcome,reason,request_id,payload,previous_hmac,hmac)
      VALUES
       (p_seq,(p_data->>'time')::timestamptz,(p_data->>'user_id')::uuid,
        (p_data->>'file_id')::uuid,p_data->>'action',p_data->>'outcome',
        p_data->>'reason',(p_data->>'request_id')::uuid,p_data,p_prev,p_sig);
      UPDATE fm.audit_head SET seq = p_seq, signature = p_sig WHERE singleton = TRUE;
    END $$;
    REVOKE ALL ON ALL TABLES IN SCHEMA fm FROM PUBLIC;
    REVOKE ALL ON ALL FUNCTIONS IN SCHEMA fm FROM PUBLIC;
    """)
    conn = op.get_bind()
    owner = conn.exec_driver_sql("SELECT current_user").scalar_one()
    app = "fm_test_app" if owner == "fm_test_owner" else "fm_app"
    # Only the two fixed application roles can be selected.
    from psycopg import sql
    statements = [
        "GRANT USAGE ON SCHEMA fm TO {}",
        "GRANT SELECT,INSERT,UPDATE ON fm.users,fm.files,fm.storage_jobs,fm.auth_attempts TO {}",
        "GRANT SELECT ON fm.operations,fm.audit_head TO {}",
        "GRANT EXECUTE ON FUNCTION fm.append_event(BIGINT,JSONB,TEXT,TEXT) TO {}",
    ]
    for statement in statements:
        conn.exec_driver_sql(sql.SQL(statement).format(sql.Identifier(app)).as_string())


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; restore a reviewed backup instead.")

