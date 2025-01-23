import os
import sys

IGNORED_SOURCES: list[str] = []


def _partial(iterable: list[str], problem: str) -> list[str]:
    """Get a partial match of a problem in a list of iterators."""

    def _get_match(problem: str, pattern: str) -> bool:
        """Internal function to verify for a pattern."""
        return bool(problem.startswith(pattern) or problem.endswith(pattern))

    return [problem for pattern in iterable if _get_match(problem, pattern)]


def get_sphinx_documents() -> list[str]:
    """Get all documents inside the docs/source folder."""
    return [
        os.path.join(root.split("/", 2)[-1], file)
        for root, _, files in os.walk("docs/source/")
        for file in files
        if (file and "index.rst" not in file and file.endswith(".rst"))
    ]


def get_source_files() -> list[str]:
    """Get a list of source files for the project."""
    return [
        os.path.join(root, file)
        for root, _, files in os.walk("command_line_assistant/")
        for file in files
        if (file and "__init__.py" not in file and file.endswith(".py"))
    ]


def get_missing_documents(
    sources: list[str],
    documents: list[str],
) -> list[str]:
    """Get a list of documents in the project."""
    missing_sources = []
    for source in sources:
        # Very naive source mount
        current_source = source.replace(".py", ".rst").replace(
            "command_line_assistant/", ""
        )

        if _partial(IGNORED_SOURCES, current_source):
            continue

        if current_source not in documents:
            missing_sources.append(source)

    return missing_sources


def main() -> int:
    """Simple program to assert that every source file has a docs."""
    documents = get_sphinx_documents()
    sources = get_source_files()

    missing_documents = get_missing_documents(sources, documents)

    if not missing_documents:
        print(
            "Hoorray! It seems that all your source files have a "
            "corresponding document for sphinx!",
        )
        return 0

    print(
        "Oh no! It seems that some of your source files are not present in "
        "the docs!\n",
    )
    print("\n".join(missing_documents))
    return 1


if __name__ == "__main__":
    sys.exit(main())
