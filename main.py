"""
NOVA - Personal AI Assistant
Entry point. Run with:  python main.py
"""

from core.nova_core import NovaCore


def main():
    nova = NovaCore(config_path="config/nova_config.json")
    try:
        nova.run_main_ai_loop()
    except KeyboardInterrupt:
        pass
    finally:
        nova.shutdown_nova()


if __name__ == "__main__":
    main()
