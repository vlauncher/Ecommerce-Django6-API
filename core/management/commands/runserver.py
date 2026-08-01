import sys
import uvicorn
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Starts the development server using Uvicorn (ASGI)."

    def add_arguments(self, parser):
        parser.add_argument(
            "addrport",
            nargs="?",
            default="127.0.0.1:8000",
            help="Optional port number, or ipaddr:port",
        )
        parser.add_argument(
            "--noreload",
            action="store_false",
            dest="use_reloader",
            default=True,
            help="Tells Uvicorn NOT to use the auto-reloader.",
        )

    def handle(self, *args, **options):
        addrport = options["addrport"]
        if ":" in addrport:
            host, port_str = addrport.split(":", 1)
        else:
            host = "127.0.0.1"
            port_str = addrport

        try:
            port = int(port_str)
        except ValueError:
            self.stderr.write(self.style.ERROR(f"Invalid port: '{port_str}'"))
            sys.exit(1)

        reload_flag = options["use_reloader"]

        self.stdout.write(
            self.style.SUCCESS(f"🚀 Starting Uvicorn ASGI server at http://{host}:{port}/")
        )

        uvicorn.run(
            "core.asgi:application",
            host=host,
            port=port,
            reload=reload_flag,
            log_level="info",
        )
