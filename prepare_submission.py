"""Собрать исходники и документацию без локальных зависимостей и секретов."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
EXCLUDED = {'node_modules', '.venv', '__pycache__', 'dist', 'staticfiles', 'media', '.rsue-cache'}


def main():
    files = []
    for folder in ('backend', 'frontend', 'sql'):
        for path in (ROOT / folder).rglob('*'):
            relative = path.relative_to(ROOT)
            if path.is_file() and not EXCLUDED.intersection(relative.parts):
                if path.suffix not in {'.pyc', '.log'} and not path.name.startswith('.env'):
                    files.append(path)
    for name in ('README.md', 'start.ps1', '.gitignore', '.env.example', 'prepare_submission.py'):
        path = ROOT / name
        if path.exists():
            files.append(path)
    output = ROOT / 'submission' / 'rgeu-schedule.zip'
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, 'rgeu-schedule/' + path.relative_to(ROOT).as_posix())
    print(f'Archive: {output} ({len(files)} files)')


if __name__ == '__main__':
    main()
