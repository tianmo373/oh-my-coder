"""Tests for src/rag/indexer.py"""

from datetime import datetime

from src.rag.indexer import (
    CodebaseIndexer,
    CodeElement,
    CodeElementType,
    FileIndex,
    IndexConfig,
    ProgrammingLanguage,
    PythonParser,
)


class TestEnums:
    """Test Enum classes"""

    def test_code_element_type_values(self):
        assert CodeElementType.MODULE == "module"
        assert CodeElementType.CLASS == "class"
        assert CodeElementType.FUNCTION == "function"
        assert CodeElementType.METHOD == "method"
        assert CodeElementType.VARIABLE == "variable"
        assert CodeElementType.IMPORT == "import"
        assert CodeElementType.CONSTANT == "constant"
        assert CodeElementType.OTHER == "other"

    def test_programming_language_values(self):
        assert ProgrammingLanguage.PYTHON == "python"
        assert ProgrammingLanguage.JAVASCRIPT == "javascript"
        assert ProgrammingLanguage.TYPESCRIPT == "typescript"
        assert ProgrammingLanguage.JAVA == "java"
        assert ProgrammingLanguage.GO == "go"
        assert ProgrammingLanguage.RUST == "rust"
        assert ProgrammingLanguage.CPP == "cpp"
        assert ProgrammingLanguage.C == "c"
        assert ProgrammingLanguage.UNKNOWN == "unknown"


class TestCodeElement:
    """Test CodeElement dataclass"""

    def test_create_minimal(self):
        element = CodeElement(
            id="test-id",
            name="test_func",
            type=CodeElementType.FUNCTION,
            file_path="src/main.py",
            start_line=1,
            end_line=10,
            source_code="def test_func():\n    pass",
        )
        assert element.id == "test-id"
        assert element.name == "test_func"
        assert element.type == CodeElementType.FUNCTION
        assert element.docstring is None
        assert element.signature is None
        assert element.parent is None
        assert element.children == []
        assert element.embedding is None
        assert element.metadata == {}

    def test_create_with_all_fields(self):
        element = CodeElement(
            id="test-id-2",
            name="MyClass",
            type=CodeElementType.CLASS,
            file_path="src/models.py",
            start_line=5,
            end_line=50,
            source_code="class MyClass:\n    pass",
            docstring="This is a test class.",
            signature="class MyClass",
            parent=None,
            children=["child1", "child2"],
            embedding=[0.1, 0.2, 0.3],
            metadata={"author": "test"},
        )
        assert element.docstring == "This is a test class."
        assert element.signature == "class MyClass"
        assert len(element.children) == 2
        assert len(element.embedding) == 3
        assert element.metadata["author"] == "test"


class TestFileIndex:
    """Test FileIndex dataclass"""

    def test_create_minimal(self):
        element = CodeElement(
            id="e1",
            name="func",
            type=CodeElementType.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=5,
            source_code="def func(): pass",
        )
        file_index = FileIndex(
            file_path="src/test.py",
            language=ProgrammingLanguage.PYTHON,
            elements=[element],
            imports=[],
            exports=[],
            dependencies=[],
            hash="abc123",
            last_modified=datetime.now(),
        )
        assert file_index.file_path == "src/test.py"
        assert file_index.language == ProgrammingLanguage.PYTHON
        assert len(file_index.elements) == 1
        assert file_index.metadata == {}

    def test_create_with_metadata(self):
        element = CodeElement(
            id="e1",
            name="func",
            type=CodeElementType.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=5,
            source_code="def func(): pass",
        )
        file_index = FileIndex(
            file_path="src/test.py",
            language=ProgrammingLanguage.PYTHON,
            elements=[element],
            imports=["os", "sys"],
            exports=[],
            dependencies=["numpy"],
            hash="def456",
            last_modified=datetime.now(),
            metadata={"lines": 100},
        )
        assert len(file_index.imports) == 2
        assert "numpy" in file_index.dependencies
        assert file_index.metadata["lines"] == 100


class TestIndexConfig:
    """Test IndexConfig dataclass"""

    def test_create_default(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        assert config.root_path == tmp_path
        assert len(config.exclude_patterns) > 0
        assert "node_modules" in config.exclude_patterns
        assert "*.pyc" in config.exclude_patterns
        assert len(config.include_patterns) > 0
        assert "*.py" in config.include_patterns
        assert config.max_file_size == 100 * 1024
        assert config.max_elements == 10000
        assert config.embedding_model == "text-embedding-3-small"
        assert config.chunk_size == 500
        assert config.chunk_overlap == 50

    def test_create_custom(self, tmp_path):
        config = IndexConfig(
            root_path=tmp_path,
            exclude_patterns=["*.test"],
            include_patterns=["*.custom"],
            max_file_size=50 * 1024,
            max_elements=5000,
            embedding_model="custom-model",
            chunk_size=1000,
            chunk_overlap=100,
        )
        assert config.exclude_patterns == ["*.test"]
        assert config.include_patterns == ["*.custom"]
        assert config.max_file_size == 50 * 1024
        assert config.max_elements == 5000
        assert config.embedding_model == "custom-model"
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 100


class TestPythonParser:
    """Test PythonParser class"""

    def test_parse_simple_function(self):
        source = """
def hello():
    '''Say hello'''
    print("Hello, World!")
"""
        parser = PythonParser()
        elements = parser.parse(source, "test.py")

        assert len(elements) == 1
        assert elements[0].name == "hello"
        assert elements[0].type == CodeElementType.FUNCTION
        assert "Say hello" in elements[0].docstring
        assert "def hello()" in elements[0].signature

    def test_parse_function_with_args(self):
        source = """
def greet(name: str, age: int) -> str:
    '''Greet someone'''
    return f"Hello {name}, age {age}"
"""
        parser = PythonParser()
        elements = parser.parse(source, "test.py")

        assert len(elements) == 1
        assert elements[0].name == "greet"
        assert "name: str" in elements[0].signature
        assert "age: int" in elements[0].signature
        assert "-> str" in elements[0].signature

    def test_parse_class(self):
        source = """
class MyClass:
    '''A test class'''

    def method(self):
        pass
"""
        parser = PythonParser()
        elements = parser.parse(source, "test.py")

        # Should have 2 elements: class + method
        assert len(elements) >= 1
        class_element = next(e for e in elements if e.type == CodeElementType.CLASS)
        assert class_element.name == "MyClass"
        assert "A test class" in class_element.docstring

    def test_parse_class_with_bases(self):
        source = """
class MyClass(BaseClass, Mixin):
    pass
"""
        parser = PythonParser()
        elements = parser.parse(source, "test.py")

        assert len(elements) == 1
        assert elements[0].name == "MyClass"
        assert "BaseClass" in elements[0].signature
        assert "Mixin" in elements[0].signature

    def test_parse_async_function(self):
        source = """
async def fetch_data():
    '''Fetch data from API'''
    pass
"""
        parser = PythonParser()
        elements = parser.parse(source, "test.py")

        assert len(elements) == 1
        assert elements[0].name == "fetch_data"
        assert "Fetch data" in elements[0].docstring

    def test_parse_empty_source(self):
        parser = PythonParser()
        elements = parser.parse("", "test.py")

        assert len(elements) == 0

    def test_parse_syntax_error(self):
        source = """
def invalid syntax here
"""
        parser = PythonParser()
        elements = parser.parse(source, "test.py")

        assert len(elements) == 0

    def test_parse_multiple_functions(self):
        source = """
def func1():
    pass

def func2():
    pass

def func3():
    pass
"""
        parser = PythonParser()
        elements = parser.parse(source, "test.py")

        assert len(elements) == 3
        names = {e.name for e in elements}
        assert names == {"func1", "func2", "func3"}

    def test_generate_id(self):
        parser = PythonParser()
        id1 = parser._generate_id("src/test.py", "my_func", 10)
        id2 = parser._generate_id("src/test.py", "my_func", 10)
        id3 = parser._generate_id("src/test.py", "other_func", 10)

        # Same inputs -> same ID
        assert id1 == id2
        # Different inputs -> different ID
        assert id1 != id3
        # ID is a hex string (SHA256 truncated to 12 chars)
        assert len(id1) == 12
        assert all(c in "0123456789abcdef" for c in id1)


class TestCodebaseIndexerInit:
    """Test CodebaseIndexer initialization"""

    def test_init_with_config(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        assert indexer.config == config
        assert indexer.embedding_client is None
        assert indexer.file_indices == {}
        assert indexer.element_index == {}
        assert ProgrammingLanguage.PYTHON in indexer._parsers

    def test_init_with_embedding_client(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        mock_client = object()
        indexer = CodebaseIndexer(config, embedding_client=mock_client)

        assert indexer.embedding_client is mock_client


class TestCodebaseIndexerShouldIndex:
    """Test CodebaseIndexer.should_index"""

    def test_accepts_python_file(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        py_file = tmp_path / "test.py"
        py_file.write_text("code")

        assert indexer.should_index(py_file) is True

    def test_rejects_large_file(self, tmp_path):
        config = IndexConfig(root_path=tmp_path, max_file_size=10)
        indexer = CodebaseIndexer(config)

        large_file = tmp_path / "large.py"
        large_file.write_text("x" * 100)  # 100 bytes > 10 limit

        assert indexer.should_index(large_file) is False

    def test_rejects_excluded_pattern(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        # node_modules is in exclude_patterns
        excluded_file = tmp_path / "node_modules" / "package.js"
        excluded_file.parent.mkdir()
        excluded_file.write_text("code")

        assert indexer.should_index(excluded_file) is False

    def test_rejects_pycache(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        pyc_file = tmp_path / "__pycache__" / "module.pyc"
        pyc_file.parent.mkdir()
        pyc_file.write_text("binary", encoding="utf-8")

        assert indexer.should_index(pyc_file) is False

    def test_accepts_javascript_file(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        js_file = tmp_path / "app.js"
        js_file.write_text("console.log('hello')")

        assert indexer.should_index(js_file) is True


class TestCodebaseIndexerDetectLanguage:
    """Test CodebaseIndexer.detect_language"""

    def test_detect_python(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        py_file = tmp_path / "test.py"
        assert indexer.detect_language(py_file) == ProgrammingLanguage.PYTHON

    def test_detect_javascript(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        js_file = tmp_path / "app.js"
        assert indexer.detect_language(js_file) == ProgrammingLanguage.JAVASCRIPT

    def test_detect_typescript(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        ts_file = tmp_path / "app.ts"
        assert indexer.detect_language(ts_file) == ProgrammingLanguage.TYPESCRIPT

    def test_detect_unknown(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        unknown_file = tmp_path / "README"
        assert indexer.detect_language(unknown_file) == ProgrammingLanguage.UNKNOWN


class TestCodebaseIndexerExtractImports:
    """Test CodebaseIndexer._extract_imports"""

    def test_extract_import(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        source = "import os\nimport sys\n"
        imports = indexer._extract_imports(source, ProgrammingLanguage.PYTHON)

        assert "os" in imports
        assert "sys" in imports

    def test_extract_from_import(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        source = "from pathlib import Path\nfrom os import getcwd\n"
        imports = indexer._extract_imports(source, ProgrammingLanguage.PYTHON)

        assert "pathlib" in imports
        assert "os" in imports

    def test_no_imports(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        source = "x = 1\ny = 2\n"
        imports = indexer._extract_imports(source, ProgrammingLanguage.PYTHON)

        assert len(imports) == 0

    def test_non_python_language(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        source = "import React from 'react';"
        imports = indexer._extract_imports(source, ProgrammingLanguage.JAVASCRIPT)

        # Only Python imports are extracted
        assert len(imports) == 0


class TestCodebaseIndexerElementToText:
    """Test CodebaseIndexer._element_to_text"""

    def test_element_to_text_basic(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        element = CodeElement(
            id="e1",
            name="test_func",
            type=CodeElementType.FUNCTION,
            file_path="src/test.py",
            start_line=1,
            end_line=5,
            source_code="def test_func():\n    pass",
        )

        text = indexer._element_to_text(element)

        assert "File: src/test.py" in text
        assert "Type: function" in text
        assert "Name: test_func" in text
        assert "Source:" in text

    def test_element_to_text_with_signature(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        element = CodeElement(
            id="e1",
            name="greet",
            type=CodeElementType.FUNCTION,
            file_path="src/test.py",
            start_line=1,
            end_line=5,
            source_code="def greet(name): pass",
            signature="def greet(name)",
        )

        text = indexer._element_to_text(element)

        assert "Signature: def greet(name)" in text

    def test_element_to_text_with_docstring(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        element = CodeElement(
            id="e1",
            name="helper",
            type=CodeElementType.FUNCTION,
            file_path="src/helper.py",
            start_line=1,
            end_line=5,
            source_code="def helper(): pass",
            docstring="This is a helper function.",
        )

        text = indexer._element_to_text(element)

        assert "Docstring: This is a helper function." in text

    def test_element_to_text_long_source(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        element = CodeElement(
            id="e1",
            name="long_func",
            type=CodeElementType.FUNCTION,
            file_path="src/long.py",
            start_line=1,
            end_line=100,
            source_code="x" * 600,  # > 500 chars
        )

        text = indexer._element_to_text(element)

        assert "..." in text
        assert len(text) < 1000  # Truncated


class TestCodebaseIndexerGetStats:
    """Test CodebaseIndexer.get_stats"""

    def test_get_stats_empty(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        stats = indexer.get_stats()

        assert stats["files_indexed"] == 0
        assert stats["elements_indexed"] == 0
        assert stats["languages"] == {}
        assert stats["element_types"] == {}

    def test_get_stats_with_data(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        # Add a file index
        element = CodeElement(
            id="e1",
            name="func",
            type=CodeElementType.FUNCTION,
            file_path="test.py",
            start_line=1,
            end_line=5,
            source_code="def func(): pass",
        )
        file_index = FileIndex(
            file_path="src/test.py",
            language=ProgrammingLanguage.PYTHON,
            elements=[element],
            imports=[],
            exports=[],
            dependencies=[],
            hash="abc",
            last_modified=datetime.now(),
        )
        indexer.file_indices["src/test.py"] = file_index
        indexer.element_index["e1"] = element

        stats = indexer.get_stats()

        assert stats["files_indexed"] == 1
        assert stats["elements_indexed"] == 1
        assert stats["languages"]["python"] == 1
        assert stats["element_types"]["function"] == 1


class TestCodebaseIndexerCountByLanguage:
    """Test CodebaseIndexer._count_by_language"""

    def test_empty(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        counts = indexer._count_by_language()

        assert counts == {}

    def test_with_files(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        file_index1 = FileIndex(
            file_path="a.py",
            language=ProgrammingLanguage.PYTHON,
            elements=[],
            imports=[],
            exports=[],
            dependencies=[],
            hash="a",
            last_modified=datetime.now(),
        )
        file_index2 = FileIndex(
            file_path="b.js",
            language=ProgrammingLanguage.JAVASCRIPT,
            elements=[],
            imports=[],
            exports=[],
            dependencies=[],
            hash="b",
            last_modified=datetime.now(),
        )
        indexer.file_indices["a.py"] = file_index1
        indexer.file_indices["b.js"] = file_index2

        counts = indexer._count_by_language()

        assert counts["python"] == 1
        assert counts["javascript"] == 1


class TestCodebaseIndexerCountByType:
    """Test CodebaseIndexer._count_by_type"""

    def test_empty(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        counts = indexer._count_by_type()

        assert counts == {}

    def test_with_elements(self, tmp_path):
        config = IndexConfig(root_path=tmp_path)
        indexer = CodebaseIndexer(config)

        element1 = CodeElement(
            id="e1",
            name="func1",
            type=CodeElementType.FUNCTION,
            file_path="a.py",
            start_line=1,
            end_line=5,
            source_code="def func1(): pass",
        )
        element2 = CodeElement(
            id="e2",
            name="MyClass",
            type=CodeElementType.CLASS,
            file_path="a.py",
            start_line=10,
            end_line=50,
            source_code="class MyClass: pass",
        )
        indexer.element_index["e1"] = element1
        indexer.element_index["e2"] = element2

        counts = indexer._count_by_type()

        assert counts["function"] == 1
        assert counts["class"] == 1


class TestCodebaseIndexerGenerateId:
    """Test ID generation uniqueness"""

    def test_different_files_different_ids(self, tmp_path):
        parser = PythonParser()
        id1 = parser._generate_id("file1.py", "func", 1)
        id2 = parser._generate_id("file2.py", "func", 1)

        assert id1 != id2

    def test_different_lines_different_ids(self, tmp_path):
        parser = PythonParser()
        id1 = parser._generate_id("file.py", "func", 1)
        id2 = parser._generate_id("file.py", "func", 100)

        assert id1 != id2
