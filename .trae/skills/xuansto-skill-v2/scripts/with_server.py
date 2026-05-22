#!/usr/bin/env python3
"""
Development server lifecycle management script.

Provides a secure wrapper for starting one or more development servers,
detecting available ports, performing health checks, running a test command,
and ensuring automatic cleanup of server processes on exit.

Usage:
    python with_server.py --server "cmd args" --port 3000 --command "test cmd"

Security:
    All subprocess calls use shell=False with list arguments to prevent
    command injection. Signal handling is cross-platform compatible.
"""

import argparse
import json
import shlex
import socket
import subprocess
import sys
import time
import signal
from urllib.request import urlopen, Request
from urllib.error import URLError


def parse_args():
    parser = argparse.ArgumentParser(
        description='Development server lifecycle manager - start servers, run tests, cleanup'
    )
    parser.add_argument(
        '--server', action='append', required=True,
        help='Server startup command (can be specified multiple times)'
    )
    parser.add_argument(
        '--port', action='append', type=int, required=True,
        help='Server port (can be specified multiple times, must match --server order)'
    )
    parser.add_argument(
        '--command', type=str, required=True,
        help='Test command to execute after servers are ready'
    )
    parser.add_argument(
        '--timeout', type=int, default=30,
        help='Server startup timeout in seconds (default: 30)'
    )
    parser.add_argument(
        '--health-check', action='append',
        help='Health check URL template (default: http://localhost:{port}, can be specified multiple times)'
    )
    return parser.parse_args()


def find_available_port(start_port):
    if start_port is None:
        start_port = 3000
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(('127.0.0.1', port))
            return True
        except OSError:
            return False


def check_health(url, timeout=5):
    try:
        req = Request(url, method='GET')
        response = urlopen(req, timeout=timeout)
        return response.status < 500
    except (URLError, OSError, Exception):
        return False


def wait_for_server(port, health_url, timeout):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_health(health_url):
            return True
        time.sleep(0.5)
    return False


def main():
    args = parse_args()

    if len(args.server) != len(args.port):
        print("Error: --server and --port must have the same number of values")
        sys.exit(1)

    health_checks = args.health_check or []
    while len(health_checks) < len(args.port):
        health_checks.append(f'http://localhost:{args.port[len(health_checks)]}')

    server_processes = []
    actual_ports = list(args.port)

    for i, port in enumerate(actual_ports):
        if is_port_in_use(port):
            available = find_available_port(port + 1)
            if available is None:
                print(f"Error: Port {port} is in use and no available port found")
                sys.exit(1)
            print(f"Warning: Port {port} is in use, using port {available} instead")
            actual_ports[i] = available
            health_checks[i] = f'http://localhost:{available}'

    def cleanup(signum=None, frame=None):
        for proc in server_processes:
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=3)
            except (OSError, ProcessLookupError):
                pass
        if signum is not None:
            sys.exit(1)

    signal.signal(signal.SIGINT, cleanup)
    try:
        signal.signal(signal.SIGTERM, cleanup)
    except (AttributeError, OSError):
        pass

    for i, server_cmd in enumerate(args.server):
        port = actual_ports[i]
        health_url = health_checks[i]

        print(f"Starting server {i + 1}/{len(args.server)}: {server_cmd} (port: {port})")
        try:
            proc = subprocess.Popen(
                shlex.split(server_cmd),
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            server_processes.append(proc)
        except (OSError, subprocess.SubprocessError) as e:
            print(f"Error: Failed to start server: {e}")
            cleanup()
            sys.exit(1)

        print(f"Waiting for server on port {port} (timeout: {args.timeout}s)...")
        if not wait_for_server(port, health_url, args.timeout):
            print(f"Error: Server on port {port} did not become ready within {args.timeout}s")
            cleanup()
            sys.exit(1)
        print(f"Server on port {port} is ready")

    print(f"\nExecuting test command: {args.command}")
    test_result = None
    test_exit_code = 1
    try:
        test_result = subprocess.run(
            shlex.split(args.command),
            shell=False,
            text=True
        )
        test_exit_code = test_result.returncode
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Error: Test command failed: {e}")
        test_exit_code = 1
    finally:
        print("\nCleaning up server processes...")
        cleanup()

    if test_exit_code == 0:
        print("\nTest command completed successfully")
    else:
        print(f"\nTest command failed with exit code: {test_exit_code}")

    sys.exit(test_exit_code)


if __name__ == '__main__':
    main()
