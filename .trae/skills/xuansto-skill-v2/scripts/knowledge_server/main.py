import argparse
import asyncio
import logging
import signal
import sys
import threading
from pathlib import Path

from .config import (
    KnowledgeConfig, KB_VERSION, fastapi_available, mcp_available,
    chroma_available, setup_logging,
)
from .server import KnowledgeServer
from .mcp_server import run_mcp_server

logger = logging.getLogger("knowledge-server")


def main():
    parser = argparse.ArgumentParser(description="知识库API服务")
    parser.add_argument("--host", default=None, help="服务监听地址（默认: 127.0.0.1）")
    parser.add_argument("--port", type=int, default=None, help="服务监听端口（默认: 8765）")
    parser.add_argument("--config", default=None, help="配置文件路径")
    parser.add_argument("--init-only", action="store_true", help="仅初始化数据库，不启动服务")
    parser.add_argument("--knowledge-root", default=None, help="知识库根目录")
    parser.add_argument("--transport", default=None, choices=["http", "mcp", "http+mcp"], help="传输协议: http, mcp, http+mcp")
    args = parser.parse_args()

    knowledge_root = Path(args.knowledge_root) if args.knowledge_root else Path(__file__).resolve().parent.parent.parent / ".knowledge"
    knowledge_root = knowledge_root.resolve()

    config_path = Path(args.config) if args.config else None
    server = KnowledgeServer(knowledge_root, config_path)

    setup_logging(server.config.server.get("log_level", "INFO"))

    logger.info("operation=server_init, knowledge_root=%s", knowledge_root)
    logger.info("operation=chroma_status, available=%s", chroma_available)
    logger.info("operation=mcp_status, available=%s", mcp_available)

    server.initialize()

    if args.init_only:
        logger.info("operation=init_only, status=completed")
        server.sqlite.close()
        return

    transport = args.transport or server.config.server.get("transport", "http+mcp")
    if transport == "stdio":
        transport = "mcp"

    if transport == "mcp":
        if not mcp_available:
            logger.error("operation=server_start, status=failed, reason=mcp_sdk_unavailable")
            sys.exit(1)
        if not server._mcp_server:
            logger.error("operation=server_start, status=failed, reason=mcp_server_not_initialized")
            sys.exit(1)

        def signal_handler(signum, frame):
            logger.info("operation=signal_received, signal=%s", signum)
            server.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info("operation=mcp_server_start, transport=stdio")
        asyncio.run(run_mcp_server(server))
        return

    if transport == "http":
        if not fastapi_available:
            logger.error("operation=server_start, status=failed, reason=fastapi_unavailable")
            sys.exit(1)

        host = args.host or server.config.server["host"]
        port = args.port or server.config.server["port"]

        def signal_handler(signum, frame):
            logger.info("operation=signal_received, signal=%s", signum)
            server.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info("operation=server_start, host=%s, port=%d", host, port)
        import uvicorn
        uvicorn.run(
            server.app,
            host=host,
            port=port,
            log_level=server.config.server.get("log_level", "info").lower(),
        )
        return

    if transport == "http+mcp":
        if not fastapi_available:
            logger.error("operation=server_start, status=failed, reason=fastapi_unavailable")
            sys.exit(1)
        if not mcp_available or not server._mcp_server:
            logger.warning("operation=mcp_server, status=unavailable, falling_back_to_http_only")
            host = args.host or server.config.server["host"]
            port = args.port or server.config.server["port"]

            def signal_handler(signum, frame):
                logger.info("operation=signal_received, signal=%s", signum)
                server.shutdown()

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            logger.info("operation=server_start, host=%s, port=%d", host, port)
            import uvicorn
            uvicorn.run(
                server.app,
                host=host,
                port=port,
                log_level=server.config.server.get("log_level", "info").lower(),
            )
            return

        host = args.host or server.config.server["host"]
        port = args.port or server.config.server["port"]

        def signal_handler(signum, frame):
            logger.info("operation=signal_received, signal=%s", signum)
            server.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info("operation=server_start, host=%s, port=%d, mcp=stdio", host, port)

        mcp_task = threading.Thread(
            target=lambda: asyncio.run(run_mcp_server(server)),
            daemon=True,
        )
        mcp_task.start()

        import uvicorn
        uvicorn.run(
            server.app,
            host=host,
            port=port,
            log_level=server.config.server.get("log_level", "info").lower(),
        )
        return


if __name__ == "__main__":
    main()
