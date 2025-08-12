import argparse


def get_args() -> argparse.Namespace:
    """Get cli arguments"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--help", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--pid", action="store_true")
    parser.add_argument("--no-pid", action="store_true")
    parser.add_argument("--skip-trial-com-users", action="store_true")
    parser.add_argument("--email")
    parser.add_argument("--server")
    parser.add_argument("--user")
    return parser.parse_args()


def get_args_reminder() -> argparse.Namespace:
    """Get cli arguments for payment reminder"""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-t", "--try-one-email", help="try-one-email")
    parser.add_argument("-p", "--pid", help="pid")
    parser.add_argument("-np", "--no-pid", action="store_true", help="no-pid")
    parser.add_argument(
        "-nu", "--no-unsubscribe", action="store_true", help="no-unsubscribe"
    )
    return parser.parse_args()
