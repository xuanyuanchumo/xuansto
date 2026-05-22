#!/usr/bin/env python3
"""
TDD绿阶段最小实现代码生成器

基于测试用例自动生成最小代码实现，遵循TDD绿阶段原则：
1. 硬编码优先 - 第一个测试可以用硬编码返回值通过
2. 简单实现优先 - 选择最简单直接的实现方式
3. 重复可接受 - 绿阶段允许代码重复
4. 不预先设计 - 只为当前测试编写代码

功能：
1. 解析测试用例，理解期望行为
2. 生成最小代码实现
3. 支持多种编程语言（Python、TypeScript/Vue）
4. 自动验证生成的代码能否通过测试

用法:
    python green_phase_generator.py --test tests/test_user.py --output app/
    python green_phase_generator.py --test tests/test_api.py --lang typescript --output src/
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class Language(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    VUE = "vue"
    GO = "go"


class TestFramework(Enum):
    PYTEST = "pytest"
    JEST = "jest"
    VITEST = "vitest"
    GO_TEST = "go_test"


@dataclass
class TestFunction:
    name: str
    docstring: str = ""
    assertions: List[str] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    expected_output: Any = None
    test_type: str = "unit"
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TestClass:
    name: str
    docstring: str = ""
    test_functions: List[TestFunction] = field(default_factory=list)
    fixtures: List[str] = field(default_factory=list)
    setup_code: str = ""


@dataclass
class ImplementationHint:
    function_name: str
    return_type: str = "Any"
    parameters: List[Tuple[str, str]] = field(default_factory=list)
    expected_return: Any = None
    implementation_strategy: str = "hardcode"
    code_template: str = ""


@dataclass
class GeneratedCode:
    file_path: str
    content: str
    language: Language
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)


@dataclass
class GreenPhaseResult:
    success: bool
    test_file: str
    generated_files: List[str] = field(default_factory=list)
    implementation_hints: List[ImplementationHint] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class TestParser:
    """测试用例解析器"""
    
    def __init__(self, language: Language = Language.PYTHON):
        self.language = language
    
    def parse_file(self, test_file: str) -> List[TestClass]:
        """解析测试文件"""
        path = Path(test_file)
        if not path.exists():
            raise FileNotFoundError(f"测试文件不存在: {test_file}")
        
        if self.language == Language.PYTHON:
            return self._parse_python_test(path)
        elif self.language in [Language.TYPESCRIPT, Language.VUE]:
            return self._parse_typescript_test(path)
        else:
            raise ValueError(f"不支持的语言: {self.language}")
    
    def _parse_python_test(self, path: Path) -> List[TestClass]:
        """解析Python测试文件"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            raise ValueError(f"测试文件语法错误: {e}")
        
        test_classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith("Test") or any(
                    self._is_test_method(n) for n in node.body
                ):
                    test_class = self._extract_test_class(node, content)
                    test_classes.append(test_class)
            
            elif isinstance(node, ast.FunctionDef):
                if self._is_test_function(node):
                    test_func = self._extract_test_function(node, content)
                    test_class = TestClass(
                        name="TestModule",
                        test_functions=[test_func]
                    )
                    test_classes.append(test_class)
        
        return test_classes
    
    def _is_test_method(self, node: ast.AST) -> bool:
        """检查是否是测试方法"""
        if isinstance(node, ast.FunctionDef):
            return node.name.startswith("test_")
        return False
    
    def _is_test_function(self, node: ast.FunctionDef) -> bool:
        """检查是否是测试函数"""
        return node.name.startswith("test_")
    
    def _extract_test_class(self, node: ast.ClassDef, content: str) -> TestClass:
        """提取测试类信息"""
        docstring = ast.get_docstring(node) or ""
        test_functions = []
        fixtures = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.startswith("test_"):
                    test_func = self._extract_test_function(item, content)
                    test_functions.append(test_func)
                elif item.name in ["setUp", "setup", "setup_method"]:
                    fixtures.append(item.name)
        
        return TestClass(
            name=node.name,
            docstring=docstring,
            test_functions=test_functions,
            fixtures=fixtures
        )
    
    def _extract_test_function(self, node: ast.FunctionDef, content: str) -> TestFunction:
        """提取测试函数信息"""
        docstring = ast.get_docstring(node) or ""
        assertions = []
        inputs = {}
        expected_output = None
        
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assertions.append(self._get_assertion_info(child))
            elif isinstance(child, ast.Call):
                if self._is_assertion_call(child):
                    assertions.append(self._get_assertion_call_info(child))
        
        input_pattern = r"#\s*输入[：:]\s*(.+)"
        for match in re.finditer(input_pattern, docstring):
            inputs["input"] = match.group(1).strip()
        
        output_pattern = r"#\s*期望[输出结果]*[：:]\s*(.+)"
        for match in re.finditer(output_pattern, docstring):
            expected_output = match.group(1).strip()
        
        return TestFunction(
            name=node.name,
            docstring=docstring,
            assertions=assertions,
            inputs=inputs,
            expected_output=expected_output,
            test_type=self._determine_test_type(node.name)
        )
    
    def _get_assertion_info(self, node: ast.Assert) -> str:
        """获取断言信息"""
        try:
            return f"assert {ast.unparse(node.test)}"
        except:
            return "assert ..."
    
    def _is_assertion_call(self, node: ast.Call) -> bool:
        """检查是否是断言调用"""
        assertion_methods = [
            "assertEqual", "assertEquals", "assert_equal",
            "assertTrue", "assertFalse", "assert_true", "assert_false",
            "assertIs", "assert_is", "assertIsNot", "assert_is_not",
            "assertIn", "assert_in", "assertNotIn", "assert_not_in",
            "assertRaises", "assert_raises", "pytest.raises",
            "expect", "should", "assert"
        ]
        
        if isinstance(node.func, ast.Attribute):
            return node.func.attr in assertion_methods
        elif isinstance(node.func, ast.Name):
            return node.func.id in assertion_methods
        return False
    
    def _get_assertion_call_info(self, node: ast.Call) -> str:
        """获取断言调用信息"""
        try:
            return ast.unparse(node)
        except:
            return "assertion call"
    
    def _determine_test_type(self, name: str) -> str:
        """确定测试类型"""
        if "unit" in name.lower():
            return "unit"
        elif "integration" in name.lower():
            return "integration"
        elif "e2e" in name.lower() or "end_to_end" in name.lower():
            return "e2e"
        elif "api" in name.lower():
            return "api"
        else:
            return "unit"
    
    def _parse_typescript_test(self, path: Path) -> List[TestClass]:
        """解析TypeScript/Vue测试文件"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        test_classes = []
        
        describe_pattern = r"(?:describe|suite)\s*\(\s*['\"](.+?)['\"]\s*,\s*\(\)\s*=>\s*\{"
        test_pattern = r"(?:it|test)\s*\(\s*['\"](.+?)['\"]\s*,\s*(?:async\s*)?\(\s*(.*?)\s*\)\s*=>\s*\{"
        
        for match in re.finditer(describe_pattern, content):
            class_name = match.group(1)
            test_class = TestClass(name=class_name)
            test_classes.append(test_class)
        
        for match in re.finditer(test_pattern, content):
            test_name = match.group(1)
            test_func = TestFunction(
                name=test_name,
                test_type=self._determine_test_type(test_name)
            )
            
            if test_classes:
                test_classes[-1].test_functions.append(test_func)
            else:
                test_class = TestClass(
                    name="TestModule",
                    test_functions=[test_func]
                )
                test_classes.append(test_class)
        
        return test_classes


class MinimalImplementationGenerator:
    """最小实现代码生成器"""
    
    IMPLEMENTATION_STRATEGIES = {
        "hardcode": "硬编码返回值 - 最简单的实现",
        "simple_return": "简单返回 - 直接返回计算结果",
        "pass_through": "透传 - 直接返回输入参数",
        "stub": "存根 - 返回空值或默认值",
        "mock": "模拟 - 返回模拟数据"
    }
    
    def __init__(self, language: Language = Language.PYTHON):
        self.language = language
        self.indent = "    "
    
    def generate_from_tests(
        self,
        test_classes: List[TestClass],
        output_dir: str
    ) -> List[GeneratedCode]:
        """从测试类生成实现代码"""
        generated = []
        
        for test_class in test_classes:
            hints = self._analyze_test_class(test_class)
            
            if self.language == Language.PYTHON:
                code = self._generate_python_implementation(hints, test_class)
            elif self.language in [Language.TYPESCRIPT, Language.VUE]:
                code = self._generate_typescript_implementation(hints, test_class)
            else:
                continue
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            file_name = self._get_output_filename(test_class)
            file_path = output_path / file_name
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code.content)
            
            generated.append(code)
        
        return generated
    
    def _analyze_test_class(self, test_class: TestClass) -> List[ImplementationHint]:
        """分析测试类，提取实现提示"""
        hints = []
        
        for test_func in test_class.test_functions:
            hint = self._analyze_test_function(test_func)
            if hint:
                hints.append(hint)
        
        return hints
    
    def _analyze_test_function(self, test_func: TestFunction) -> Optional[ImplementationHint]:
        """分析测试函数，提取实现提示"""
        func_name = self._extract_function_name(test_func.name)
        if not func_name:
            return None
        
        parameters = self._extract_parameters(test_func)
        return_type = self._infer_return_type(test_func)
        expected_return = self._extract_expected_return(test_func)
        strategy = self._determine_strategy(test_func, expected_return)
        
        return ImplementationHint(
            function_name=func_name,
            return_type=return_type,
            parameters=parameters,
            expected_return=expected_return,
            implementation_strategy=strategy
        )
    
    def _extract_function_name(self, test_name: str) -> Optional[str]:
        """从测试名称提取函数名"""
        patterns = [
            r"test_(\w+)",
            r"test_?(\w+)_?returns?",
            r"test_?(\w+)_?when",
            r"should_?(\w+)",
            r"(\w+)_should",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, test_name.lower())
            if match:
                return match.group(1)
        
        return None
    
    def _extract_parameters(self, test_func: TestFunction) -> List[Tuple[str, str]]:
        """提取函数参数"""
        parameters = []
        
        for assertion in test_func.assertions:
            param_pattern = r"\b(\w+)\s*[=,)]"
            for match in re.finditer(param_pattern, assertion):
                param_name = match.group(1)
                if param_name not in ["self", "cls", "assert", "True", "False", "None"]:
                    parameters.append((param_name, "Any"))
        
        return list(dict.fromkeys(parameters))
    
    def _infer_return_type(self, test_func: TestFunction) -> str:
        """推断返回类型"""
        assertions = test_func.assertions
        docstring = test_func.docstring.lower()
        
        if "true" in docstring or any("true" in a.lower() for a in assertions):
            return "bool"
        elif "false" in docstring or any("false" in a.lower() for a in assertions):
            return "bool"
        elif "none" in docstring or any("none" in a.lower() for a in assertions):
            return "Optional[Any]"
        elif "list" in docstring or any("[" in a for a in assertions):
            return "List[Any]"
        elif "dict" in docstring or any("{" in a for a in assertions):
            return "Dict[str, Any]"
        elif "int" in docstring or any(re.search(r"\b\d+\b", a) for a in assertions):
            return "int"
        elif "str" in docstring or any('"' in a or "'" in a for a in assertions):
            return "str"
        else:
            return "Any"
    
    def _extract_expected_return(self, test_func: TestFunction) -> Any:
        """提取期望返回值"""
        if test_func.expected_output:
            return test_func.expected_output
        
        for assertion in test_func.assertions:
            patterns = [
                (r"==\s*(\d+)", lambda m: int(m.group(1))),
                (r"==\s*['\"](.+?)['\"]", lambda m: m.group(1)),
                (r"==\s*(True|False)", lambda m: m.group(1) == "True"),
                (r"==\s*(None)", lambda m: None),
                (r"==\s*(\[.*?\])", lambda m: m.group(1)),
                (r"==\s*(\{.*?\})", lambda m: m.group(1)),
            ]
            
            for pattern, converter in patterns:
                match = re.search(pattern, assertion)
                if match:
                    try:
                        return converter(match)
                    except:
                        continue
        
        return None
    
    def _determine_strategy(
        self,
        test_func: TestFunction,
        expected_return: Any
    ) -> str:
        """确定实现策略"""
        if expected_return is not None:
            return "hardcode"
        
        docstring = test_func.docstring.lower()
        
        if "should return" in docstring or "returns" in docstring:
            return "simple_return"
        elif "pass" in docstring:
            return "pass_through"
        else:
            return "stub"
    
    def _generate_python_implementation(
        self,
        hints: List[ImplementationHint],
        test_class: TestClass
    ) -> GeneratedCode:
        """生成Python实现代码"""
        lines = [
            '"""',
            f'自动生成的最小实现代码',
            f'测试类: {test_class.name}',
            f'生成时间: {datetime.now().isoformat()}',
            "",
            "遵循TDD绿阶段原则:",
            "- 硬编码优先",
            "- 简单实现优先",
            "- 重复可接受",
            "- 不预先设计",
            '"""',
            "",
            "from typing import Any, Optional, List, Dict",
            "",
            "",
        ]
        
        functions = []
        for hint in hints:
            func_code = self._generate_python_function(hint)
            lines.extend(func_code)
            lines.append("")
            functions.append(hint.function_name)
        
        return GeneratedCode(
            file_path="",
            content="\n".join(lines),
            language=Language.PYTHON,
            imports=["from typing import Any, Optional, List, Dict"],
            functions=functions
        )
    
    def _generate_python_function(self, hint: ImplementationHint) -> List[str]:
        """生成Python函数"""
        params_str = ", ".join(f"{p[0]}: {p[1]}" for p in hint.parameters)
        if not params_str:
            params_str = ""
        
        lines = [
            f"def {hint.function_name}({params_str}) -> {hint.return_type}:",
            f'{self.indent}"""',
            f"{self.indent}最小实现 - {self.IMPLEMENTATION_STRATEGIES.get(hint.implementation_strategy, '未知策略')}",
            f'{self.indent}"""',
        ]
        
        if hint.implementation_strategy == "hardcode" and hint.expected_return is not None:
            if isinstance(hint.expected_return, str):
                return_value = f'"{hint.expected_return}"'
            elif isinstance(hint.expected_return, bool):
                return_value = "True" if hint.expected_return else "False"
            elif hint.expected_return is None:
                return_value = "None"
            else:
                return_value = str(hint.expected_return)
            
            lines.append(f"{self.indent}return {return_value}")
        
        elif hint.implementation_strategy == "stub":
            if hint.return_type.startswith("Optional"):
                lines.append(f"{self.indent}return None")
            elif hint.return_type == "bool":
                lines.append(f"{self.indent}return True")
            elif hint.return_type == "int":
                lines.append(f"{self.indent}return 0")
            elif hint.return_type == "str":
                lines.append(f'{self.indent}return ""')
            elif hint.return_type.startswith("List"):
                lines.append(f"{self.indent}return []")
            elif hint.return_type.startswith("Dict"):
                lines.append(f"{self.indent}return {{}}")
            else:
                lines.append(f"{self.indent}pass")
        
        elif hint.implementation_strategy == "pass_through":
            if hint.parameters:
                lines.append(f"{self.indent}return {hint.parameters[0][0]}")
            else:
                lines.append(f"{self.indent}pass")
        
        else:
            lines.append(f"{self.indent}pass")
        
        return lines
    
    def _generate_typescript_implementation(
        self,
        hints: List[ImplementationHint],
        test_class: TestClass
    ) -> GeneratedCode:
        """生成TypeScript实现代码"""
        lines = [
            '/**',
            ' * 自动生成的最小实现代码',
            f' * 测试类: {test_class.name}',
            f' * 生成时间: {datetime.now().isoformat()}',
            ' */',
            '',
        ]
        
        functions = []
        for hint in hints:
            func_code = self._generate_typescript_function(hint)
            lines.extend(func_code)
            lines.append("")
            functions.append(hint.function_name)
        
        return GeneratedCode(
            file_path="",
            content="\n".join(lines),
            language=Language.TYPESCRIPT,
            imports=[],
            functions=functions
        )
    
    def _generate_typescript_function(self, hint: ImplementationHint) -> List[str]:
        """生成TypeScript函数"""
        ts_type_map = {
            "Any": "any",
            "Optional[Any]": "any | null",
            "bool": "boolean",
            "int": "number",
            "float": "number",
            "str": "string",
            "List[Any]": "any[]",
            "Dict[str, Any]": "Record<string, any>",
        }
        
        return_type = ts_type_map.get(hint.return_type, "any")
        
        params_str = ", ".join(
            f"{p[0]}: {ts_type_map.get(p[1], 'any')}"
            for p in hint.parameters
        )
        
        lines = [
            f"export function {hint.function_name}({params_str}): {return_type} {{",
            f"{self.indent}/**",
            f"{self.indent} * 最小实现 - {self.IMPLEMENTATION_STRATEGIES.get(hint.implementation_strategy, '未知策略')}",
            f"{self.indent} */",
        ]
        
        if hint.implementation_strategy == "hardcode" and hint.expected_return is not None:
            if isinstance(hint.expected_return, str):
                return_value = f'"{hint.expected_return}"'
            elif isinstance(hint.expected_return, bool):
                return_value = "true" if hint.expected_return else "false"
            elif hint.expected_return is None:
                return_value = "null"
            else:
                return_value = str(hint.expected_return)
            
            lines.append(f"{self.indent}return {return_value};")
        
        elif hint.implementation_strategy == "stub":
            if "null" in return_type:
                lines.append(f"{self.indent}return null;")
            elif return_type == "boolean":
                lines.append(f"{self.indent}return true;")
            elif return_type == "number":
                lines.append(f"{self.indent}return 0;")
            elif return_type == "string":
                lines.append(f'{self.indent}return "";')
            elif return_type.endswith("[]"):
                lines.append(f"{self.indent}return [];")
            else:
                lines.append(f"{self.indent}return undefined;")
        
        else:
            lines.append(f"{self.indent}return undefined;")
        
        lines.append("}")
        
        return lines
    
    def _get_output_filename(self, test_class: TestClass) -> str:
        """获取输出文件名"""
        name = test_class.name.lower()
        name = name.replace("test", "").strip("_")
        
        if self.language == Language.PYTHON:
            return f"{name or 'implementation'}.py"
        elif self.language in [Language.TYPESCRIPT, Language.VUE]:
            return f"{name or 'implementation'}.ts"
        else:
            return f"{name or 'implementation'}"


class GreenPhaseValidator:
    """绿阶段验证器"""
    
    def __init__(self, language: Language = Language.PYTHON):
        self.language = language
    
    def validate_implementation(
        self,
        test_file: str,
        implementation_files: List[str]
    ) -> Dict[str, Any]:
        """验证实现是否通过测试"""
        if self.language == Language.PYTHON:
            return self._validate_python(test_file, implementation_files)
        elif self.language in [Language.TYPESCRIPT, Language.VUE]:
            return self._validate_typescript(test_file, implementation_files)
        else:
            return {"success": False, "error": f"不支持的语言: {self.language}"}
    
    def _validate_python(
        self,
        test_file: str,
        implementation_files: List[str]
    ) -> Dict[str, Any]:
        """验证Python实现"""
        try:
            cmd = [
                sys.executable, "-m", "pytest",
                test_file,
                "-v", "--tb=short",
                "--timeout=60"
            ]
            
            env = os.environ.copy()
            for impl_file in implementation_files:
                impl_dir = str(Path(impl_file).parent)
                if "PYTHONPATH" in env:
                    env["PYTHONPATH"] = f"{impl_dir}:{env['PYTHONPATH']}"
                else:
                    env["PYTHONPATH"] = impl_dir
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            passed = process.returncode == 0
            
            return {
                "success": passed,
                "returncode": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "test_file": test_file,
                "implementation_files": implementation_files
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "测试执行超时"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_typescript(
        self,
        test_file: str,
        implementation_files: List[str]
    ) -> Dict[str, Any]:
        """验证TypeScript实现"""
        try:
            cmd = ["npm", "test", "--", test_file]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(Path(test_file).parent)
            )
            
            passed = process.returncode == 0
            
            return {
                "success": passed,
                "returncode": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "test_file": test_file,
                "implementation_files": implementation_files
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "测试执行超时"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class GreenPhaseGenerator:
    """绿阶段代码生成器主类"""
    
    def __init__(
        self,
        language: Language = Language.PYTHON,
        output_dir: str = "generated"
    ):
        self.language = language
        self.output_dir = output_dir
        self.test_parser = TestParser(language)
        self.impl_generator = MinimalImplementationGenerator(language)
        self.validator = GreenPhaseValidator(language)
    
    def generate_minimal_implementation(
        self,
        test_file: str,
        validate: bool = True
    ) -> GreenPhaseResult:
        """生成最小实现代码"""
        result = GreenPhaseResult(
            success=False,
            test_file=test_file
        )
        
        try:
            test_classes = self.test_parser.parse_file(test_file)
            
            if not test_classes:
                result.errors.append("未找到测试类或测试函数")
                return result
            
            generated_codes = self.impl_generator.generate_from_tests(
                test_classes,
                self.output_dir
            )
            
            result.generated_files = [gc.file_path for gc in generated_codes if gc.file_path]
            
            for tc in test_classes:
                hints = self.impl_generator._analyze_test_class(tc)
                result.implementation_hints.extend(hints)
            
            if validate and generated_codes:
                impl_files = [
                    str(Path(self.output_dir) / Path(gc.file_path).name)
                    for gc in generated_codes
                ]
                
                for impl_file in impl_files:
                    if Path(impl_file).exists():
                        result.generated_files.append(impl_file)
                
                validation_result = self.validator.validate_implementation(
                    test_file,
                    result.generated_files
                )
                result.test_results = validation_result
                
                if validation_result.get("success"):
                    result.success = True
                else:
                    result.warnings.append(
                        f"生成的代码可能需要调整以通过测试: {validation_result.get('error', '未知错误')}"
                    )
            else:
                result.success = True
            
        except FileNotFoundError as e:
            result.errors.append(f"文件未找到: {e}")
        except Exception as e:
            result.errors.append(f"生成错误: {e}")
        
        return result
    
    def generate_report(self, result: GreenPhaseResult) -> str:
        """生成绿阶段执行报告"""
        lines = [
            "# TDD绿阶段执行报告",
            "",
            f"**测试文件**: {result.test_file}",
            f"**执行状态**: {'✅ 成功' if result.success else '❌ 失败'}",
            f"**生成时间**: {datetime.now().isoformat()}",
            "",
            "## 生成的文件",
            "",
        ]
        
        for file_path in result.generated_files:
            lines.append(f"- `{file_path}`")
        
        if not result.generated_files:
            lines.append("- 无")
        
        lines.extend([
            "",
            "## 实现提示",
            "",
        ])
        
        for hint in result.implementation_hints:
            lines.append(f"### {hint.function_name}")
            lines.append(f"- **返回类型**: {hint.return_type}")
            lines.append(f"- **参数**: {', '.join(f'{p[0]}: {p[1]}' for p in hint.parameters) or '无'}")
            lines.append(f"- **实现策略**: {hint.implementation_strategy}")
            if hint.expected_return is not None:
                lines.append(f"- **期望返回值**: `{hint.expected_return}`")
            lines.append("")
        
        if result.test_results:
            lines.extend([
                "## 测试验证结果",
                "",
                f"- **通过**: {'是' if result.test_results.get('success') else '否'}",
                "",
            ])
            
            if result.test_results.get("stdout"):
                lines.extend([
                    "### 测试输出",
                    "",
                    "```",
                    result.test_results["stdout"][:2000],
                    "```",
                    "",
                ])
        
        if result.errors:
            lines.extend([
                "## 错误",
                "",
            ])
            for error in result.errors:
                lines.append(f"- ❌ {error}")
            lines.append("")
        
        if result.warnings:
            lines.extend([
                "## 警告",
                "",
            ])
            for warning in result.warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")
        
        lines.extend([
            "## TDD绿阶段原则",
            "",
            "1. **硬编码优先** - 第一个测试可以用硬编码返回值通过",
            "2. **简单实现优先** - 选择最简单直接的实现方式",
            "3. **重复可接受** - 绿阶段允许代码重复",
            "4. **不预先设计** - 只为当前测试编写代码",
            "",
            "## 下一步",
            "",
            "1. 运行测试确认通过",
            "2. 如有更多测试，逐步通用化实现",
            "3. 进入重构阶段优化代码",
        ])
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="TDD绿阶段最小实现代码生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从Python测试文件生成实现
  python green_phase_generator.py --test tests/test_user.py --output app/
  
  # 从TypeScript测试文件生成实现
  python green_phase_generator.py --test tests/user.test.ts --lang typescript --output src/
  
  # 生成并验证
  python green_phase_generator.py --test tests/test_api.py --validate
        """
    )
    
    parser.add_argument(
        "--test",
        required=True,
        help="测试文件路径"
    )
    
    parser.add_argument(
        "--output",
        default="generated",
        help="输出目录路径"
    )
    
    parser.add_argument(
        "--lang",
        choices=["python", "typescript", "vue"],
        default="python",
        help="目标语言"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="生成后验证测试"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="生成执行报告"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    language = Language(args.lang)
    
    generator = GreenPhaseGenerator(
        language=language,
        output_dir=args.output
    )
    
    print("=" * 60)
    print("TDD绿阶段最小实现代码生成器")
    print("=" * 60)
    print(f"测试文件: {args.test}")
    print(f"目标语言: {language.value}")
    print(f"输出目录: {args.output}")
    print()
    
    result = generator.generate_minimal_implementation(
        args.test,
        validate=args.validate
    )
    
    if args.verbose:
        print("\n生成的文件:")
        for f in result.generated_files:
            print(f"  - {f}")
        
        print("\n实现提示:")
        for hint in result.implementation_hints:
            print(f"  - {hint.function_name}: {hint.implementation_strategy}")
    
    if args.report:
        report = generator.generate_report(result)
        report_file = Path(args.output) / "green_phase_report.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n报告已生成: {report_file}")
    
    print("\n" + "=" * 60)
    print(f"执行状态: {'✅ 成功' if result.success else '❌ 失败'}")
    print("=" * 60)
    
    if result.errors:
        print("\n错误:")
        for error in result.errors:
            print(f"  - {error}")
    
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
