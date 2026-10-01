"""Create the current application schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-05

"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admauth",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("username", sa.String(length=250), nullable=True),
        sa.Column("password", sa.Text(), nullable=True),
        sa.Column("role", sa.Enum("ADMIN", "MANAGER", name="roleenum"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "certs",
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("ca", sa.Text(), nullable=True),
        sa.Column("cert", sa.Text(), nullable=True),
        sa.Column("key", sa.Text(), nullable=True),
        sa.Column("tls", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("username"),
    )
    op.create_table(
        "coupons",
        sa.Column("coupon", sa.String(length=250), nullable=False),
        sa.Column("max_use_limit", sa.Integer(), nullable=True),
        sa.Column("percent", sa.Integer(), nullable=True),
        sa.Column("prolong", sa.Integer(), nullable=True),
        sa.Column("times_used", sa.Integer(), nullable=True),
        sa.Column("manual", sa.Boolean(), nullable=True),
        sa.Column("expiration", sa.TIMESTAMP(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created", sa.TIMESTAMP(), nullable=True),
        sa.Column("plans", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("coupon"),
    )
    op.create_index("coupons_coupon", "coupons", ["coupon"], unique=True)
    op.create_index("manual_created", "coupons", ["manual", "created"], unique=False)
    op.create_table(
        "partners",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("created", sa.TIMESTAMP(), nullable=False),
        sa.Column("password", mysql.VARCHAR(length=100), nullable=True),
        sa.Column("commission", sa.BigInteger(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("lang", mysql.VARCHAR(length=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("id", "partners", ["id"], unique=True)
    op.create_table(
        "servers_config",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("server", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("hidden", sa.Boolean(), nullable=False),
        sa.Column("auto_visibility", sa.Boolean(), nullable=False),
        sa.Column("iso", mysql.VARCHAR(length=2), nullable=True),
        sa.Column("country", mysql.VARCHAR(length=50), nullable=True),
        sa.Column("city", mysql.VARCHAR(length=50), nullable=True),
        sa.Column("ip", mysql.VARCHAR(length=15), nullable=True),
        sa.Column("remote_ips", sa.Text(), nullable=True),
        sa.Column("trial", sa.Boolean(), nullable=True),
        sa.Column("openvpn", sa.Boolean(), nullable=True),
        sa.Column("ikev2", sa.Boolean(), nullable=True),
        sa.Column("proxy", sa.Boolean(), nullable=True),
        sa.Column("l2tp", sa.Boolean(), nullable=True),
        sa.Column("l2tp_raw", sa.Boolean(), nullable=True),
        sa.Column("l2tp_ipsec", sa.Boolean(), nullable=True),
        sa.Column("sstp", sa.Boolean(), nullable=True),
        sa.Column("softether", sa.Boolean(), nullable=True),
        sa.Column("hoster_data", mysql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("server", "servers_config", ["server"], unique=True)
    op.create_table(
        "tariffs_whox",
        sa.Column("id", mysql.VARCHAR(length=10), nullable=False),
        sa.Column("month", mysql.VARCHAR(length=10), nullable=True),
        sa.Column("count", mysql.VARCHAR(length=5), nullable=True),
        sa.Column("economy", mysql.VARCHAR(length=5), nullable=True),
        sa.Column("popular", mysql.VARCHAR(length=5), nullable=True),
        sa.Column("countTextSum", mysql.VARCHAR(length=5), nullable=True),
        sa.Column("date", mysql.VARCHAR(length=5), nullable=True),
        sa.Column("countText", mysql.VARCHAR(length=5), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("email", mysql.VARCHAR(length=250), nullable=False),
        sa.Column("created", sa.TIMESTAMP(), nullable=False),
        sa.Column("cn", sa.String(length=100), nullable=True),
        sa.Column("trial", sa.Boolean(), nullable=True),
        sa.Column("version_page", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=250), nullable=True),
        sa.Column("coupon", sa.String(length=250), nullable=True),
        sa.Column("expires", sa.Integer(), nullable=True),
        sa.Column("plan", sa.Integer(), nullable=True),
        sa.Column("country_iso", sa.String(length=2), nullable=True),
        sa.Column("password", sa.String(length=100), nullable=True),
        sa.Column("reg_source", sa.String(length=100), nullable=True),
        sa.Column("dubious", sa.Boolean(), nullable=False),
        sa.Column("subscribed", sa.Boolean(), nullable=False),
        sa.Column("lang", sa.String(length=2), nullable=False),
        sa.Column("partner_id", sa.BigInteger(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("id", "users", ["id"], unique=True)
    op.create_index("users_email_unique", "users", ["email"], unique=True)
    op.create_index("users_code_unique", "users", ["code"], unique=True)
    op.create_index("users_cn_unique", "users", ["cn"], unique=True)
    op.create_index("users_code_expires", "users", ["code", "expires"], unique=False)
    op.create_index("users_trial", "users", ["trial"], unique=False)
    op.create_index("users_dubious", "users", ["dubious"], unique=False)
    op.create_index("users_expires", "users", ["expires"], unique=False, mysql_using="BTREE")
    op.create_index("users_created", "users", ["created"], unique=False)
    op.create_index("trial_expires", "users", ["trial", "expires"], unique=False)
    op.create_table(
        "buy_form_filling",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("created", sa.TIMESTAMP(), nullable=False),
        sa.Column("email", mysql.VARCHAR(length=250), nullable=True),
        sa.Column("lang", mysql.VARCHAR(length=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("created", "buy_form_filling", ["created"], unique=False)
    op.create_index("email", "buy_form_filling", ["email"], unique=False)
    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("system", sa.String(length=100), nullable=True),
        sa.Column("data", sa.Text(), nullable=True),
        sa.Column("days", sa.Integer(), nullable=True),
        sa.Column("amount", sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column("email", mysql.VARCHAR(length=250), nullable=True),
        sa.Column("expires", sa.TIMESTAMP(), nullable=False),
        sa.Column("created", sa.TIMESTAMP(), nullable=False),
        sa.Column("trial", sa.Boolean(), nullable=True),
        sa.Column("coupon", sa.String(length=250), nullable=True),
        sa.Column("version_page", sa.Integer(), nullable=True),
        sa.Column("country_iso", sa.String(length=2), nullable=True),
        sa.Column("complete", sa.Boolean(), nullable=True),
        sa.Column("partner_amount", sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column("partner_id", sa.BigInteger(), nullable=True),
        sa.Column("partner_referrer_id", sa.BigInteger(), nullable=True),
        sa.Column("pushed_by", sa.String(length=250), nullable=True),
        sa.Column("remote_amount", sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column("check_order_id", sa.BigInteger(), nullable=True),
        sa.Column("pay_time", sa.Integer(), nullable=True),
        sa.Column("remote_status", mysql.VARCHAR(length=255), nullable=True),
        sa.Column("credited", sa.String(length=255), nullable=True),
        sa.Column("json_custom_fields", sa.String(length=8000), nullable=True),
        sa.Column("remote_invoice_id", sa.String(length=8000), nullable=True),
        sa.Column("refund", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("transactions_email", "transactions", ["email"], unique=False)
    op.create_index(
        "transactions_email_complete",
        "transactions",
        ["email", "complete"],
        unique=False,
    )
    op.create_index("transactions_trial", "transactions", ["trial"], unique=False)
    op.create_index("transactions_created", "transactions", ["created"], unique=False)
    op.create_index("transactions_expires", "transactions", ["expires"], unique=False)
    op.create_index("transactions_partner_id", "transactions", ["partner_id"], unique=False)
    op.create_index("transactions_coupon", "transactions", ["coupon", "created"], unique=False)
    op.create_index(
        "transactions_complete_created",
        "transactions",
        ["complete", "created"],
        unique=False,
    )
    op.create_table(
        "vpn_servers_stat",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("server", sa.String(length=64), nullable=False),
        sa.Column("created", sa.TIMESTAMP(), nullable=False),
        sa.Column("online_vpn", sa.Integer(), nullable=False),
        sa.Column("online_proxy", sa.Integer(), nullable=True),
        sa.Column("traf_today", sa.Integer(), nullable=False),
        sa.Column("traf_yesterday", sa.Integer(), nullable=False),
        sa.Column("traf_month", sa.Integer(), nullable=False),
        sa.Column("online_l2tp", sa.Integer(), nullable=True),
        sa.Column("online_sstp", sa.Integer(), nullable=True),
        sa.Column("online_softether_native", sa.Integer(), nullable=True),
        sa.Column("wman_version", sa.String(length=64), nullable=True),
        sa.Column("bandwidth_today", sa.String(length=64), nullable=True),
        sa.Column("bandwidth_yesterday", sa.String(length=64), nullable=True),
        sa.Column("bandwidth_month", sa.String(length=64), nullable=True),
        sa.Column("load_cpu", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vpn_servers_stat_server_created",
        "vpn_servers_stat",
        ["server", "created"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_vpn_servers_stat_server_created",
        table_name="vpn_servers_stat",
    )
    op.drop_table("vpn_servers_stat")
    op.drop_index("transactions_complete_created", table_name="transactions")
    op.drop_index("transactions_coupon", table_name="transactions")
    op.drop_index("transactions_partner_id", table_name="transactions")
    op.drop_index("transactions_expires", table_name="transactions")
    op.drop_index("transactions_created", table_name="transactions")
    op.drop_index("transactions_trial", table_name="transactions")
    op.drop_index("transactions_email_complete", table_name="transactions")
    op.drop_index("transactions_email", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("email", table_name="buy_form_filling")
    op.drop_index("created", table_name="buy_form_filling")
    op.drop_table("buy_form_filling")
    op.drop_index("trial_expires", table_name="users")
    op.drop_index("users_created", table_name="users")
    op.drop_index("users_expires", table_name="users")
    op.drop_index("users_dubious", table_name="users")
    op.drop_index("users_trial", table_name="users")
    op.drop_index("users_code_expires", table_name="users")
    op.drop_index("users_cn_unique", table_name="users")
    op.drop_index("users_code_unique", table_name="users")
    op.drop_index("users_email_unique", table_name="users")
    op.drop_index("id", table_name="users")
    op.drop_table("users")
    op.drop_table("tariffs_whox")
    op.drop_index("server", table_name="servers_config")
    op.drop_table("servers_config")
    op.drop_index("id", table_name="partners")
    op.drop_table("partners")
    op.drop_index("manual_created", table_name="coupons")
    op.drop_index("coupons_coupon", table_name="coupons")
    op.drop_table("coupons")
    op.drop_table("certs")
    op.drop_table("admauth")
