from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Enable WAL journaling for SQLite (R3 risk mitigation, Section 12 of build spec)
        from django.db.backends.signals import connection_created

        def enable_sqlite_wal(sender, connection, **kwargs):
            if connection.vendor == "sqlite":
                with connection.cursor() as cursor:
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA synchronous=NORMAL;")
                    cursor.execute("PRAGMA foreign_keys=ON;")

        connection_created.connect(enable_sqlite_wal)
