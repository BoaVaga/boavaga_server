import pathlib
import sys

from src.app import create_app
from src.container import create_container
from src.repo.repo_container import create_repo_container


def main():
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        cur_dir = pathlib.Path(__file__).parent
        config_path = str(cur_dir / 'dev.ini')

    app = create_app(create_container(config_path), create_repo_container(config_path))
    app.run()


if __name__ == '__main__':
    main()
