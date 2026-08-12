# Python env   : Python v3.12.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/06 涓嬪崍6:36
# @Author  : 鏉庢竻姘?# @File    : code_checker.py
# @Description : MicroPython浠ｇ爜瑙勮寖妫€鏌ュ伐鍏凤紝鏍￠獙椹卞姩鏂囦欢銆乵ain.py鍜宲ackage.json鏄惁绗﹀悎GraftSense瑙勮寖

"""
Pre-commit code checker for MicroPython driver packages.
"""

# ======================================== 瀵煎叆鐩稿叧妯″潡 =========================================

import argparse
import ast
import json
import re
import sys
from pathlib import Path

# ======================================== 鍏ㄥ眬鍙橀噺 ============================================

REQUIRED_GLOBALS = ["__version__", "__author__", "__license__", "__platform__"]
LICENSE_COMMENT = "# @License : MIT"
SECTION_TITLES = [
    "\u5bfc\u5165\u76f8\u5173\u6a21\u5757",
    "\u5168\u5c40\u53d8\u91cf",
    "\u529f\u80fd\u51fd\u6570",
    "\u81ea\u5b9a\u4e49\u7c7b",
    "\u521d\u59cb\u5316\u914d\u7f6e",
    "\u4e3b\u7a0b\u5e8f",
]
SECTION_TITLE_SET = set(SECTION_TITLES)
FREAKSTUDIO_PATTERN = r'print\s*\(\s*["\']FreakStudio:'
SLEEP3_PATTERN = r"time\.sleep\s*\(\s*3\s*\)"
CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]")
HARDWARE_CTORS = {"I2C", "SPI", "UART", "Pin", "Timer", "ADC", "PWM"}
TEST_DEMO_PATTERN = re.compile(r"(^test_|_test\.py$|^demo_|_demo\.py$|test\.py$)", re.IGNORECASE)

# ======================================== 鍔熻兘鍑芥暟 ============================================


def read_file_content(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8-sig")
    except Exception as e:
        print(f"[FAIL] Error reading file {file_path}: {str(e)}")
        return ""


def normalize_section_line(line: str) -> str:
    stripped = line.strip()
    if not stripped.startswith("#"):
        return ""
    core = re.sub(r"[=#\s]", "", stripped)
    return core if core in SECTION_TITLE_SET else ""


def parse_section_markers(content: str) -> list:
    markers = []
    for line_no, line in enumerate(content.splitlines(), 1):
        title = normalize_section_line(line)
        if title:
            indent = len(line) - len(line.lstrip(" \t"))
            markers.append({"title": title, "line": line_no, "indent": indent, "text": line})
    return markers


def get_section_ranges(content: str) -> dict:
    lines = content.splitlines()
    markers = parse_section_markers(content)
    first = {}
    for marker in markers:
        first.setdefault(marker["title"], marker)
    ordered = sorted(first.values(), key=lambda marker: marker["line"])
    ranges = {}
    for idx, marker in enumerate(ordered):
        start = marker["line"] + 1
        end = ordered[idx + 1]["line"] if idx + 1 < len(ordered) else len(lines) + 1
        ranges[marker["title"]] = (start, end)
    return ranges


def extract_section_content(content: str, marker: str) -> str:
    target = normalize_section_line(marker) or re.sub(r"[=#\s]", "", marker)
    ranges = get_section_ranges(content)
    if target not in ranges:
        return ""
    start, end = ranges[target]
    lines = content.splitlines()
    return "\n".join(lines[start - 1 : end - 1])


def in_range(line_no: int, section_range: tuple) -> bool:
    return bool(section_range) and section_range[0] <= line_no < section_range[1]


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def function_arg_nodes(func: ast.FunctionDef) -> list:
    args = []
    args.extend(getattr(func.args, "posonlyargs", []))
    args.extend(func.args.args)
    args.extend(func.args.kwonlyargs)
    if func.args.vararg:
        args.append(func.args.vararg)
    if func.args.kwarg:
        args.append(func.args.kwarg)
    return args


def missing_arg_annotations(func: ast.FunctionDef, skip_self: bool = True) -> list:
    missing = []
    for arg in function_arg_nodes(func):
        if skip_self and arg.arg in ("self", "cls"):
            continue
        if arg.annotation is None:
            missing.append(arg.arg)
    return missing


def annotation_text(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<annotation>"


def has_none_return(func: ast.FunctionDef) -> bool:
    return func.returns is not None and annotation_text(func.returns) in ("None", "NoneType")


def decorator_names(func: ast.FunctionDef) -> list:
    names = []
    for decorator in func.decorator_list:
        try:
            names.append(ast.unparse(decorator))
        except Exception:
            names.append(type(decorator).__name__)
    return names


def is_property_setter(func: ast.FunctionDef) -> bool:
    return any(name.endswith(".setter") for name in decorator_names(func))


def names_in_node(node: ast.AST) -> set:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}


def has_raise(stmt: ast.AST) -> bool:
    return any(isinstance(child, ast.Raise) for child in ast.walk(stmt))


def exact_case_exists(base: Path, relative_path: str) -> tuple:
    if not relative_path or Path(relative_path).is_absolute() or relative_path.startswith(("/", "\\")):
        return False, False, "rooted/absolute path"
    current = base
    for part in re.split(r"[\\/]+", relative_path):
        if part in ("", "."):
            continue
        if not current.exists() or not current.is_dir():
            return False, False, f"parent missing: {current}"
        exact = {child.name: child for child in current.iterdir()}
        if part in exact:
            current = exact[part]
            continue
        insensitive = {child.name.lower(): child for child in current.iterdir()}
        if part.lower() in insensitive:
            return False, True, str(insensitive[part.lower()])
        return False, False, f"missing component: {part} under {current}"
    return current.exists(), current.exists(), str(current)


def check_required_globals(content: str, file_path: Path) -> bool:
    if file_path.name == "main.py":
        print(f"[PASS] {file_path}: main.py Skip global variables check (main.py)")
        return True
    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"[FAIL] {file_path}: Failed to parse code AST: {str(e)}")
        return False
    assigned = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
    missing = [name for name in REQUIRED_GLOBALS if name not in assigned]
    if missing:
        print(f"[FAIL] {file_path}: Missing required global variables: {', '.join(missing)}")
        return False
    print(f"[PASS] {file_path}: All 4 required global variables exist")
    return True


def check_license_comment(content: str, file_path: Path) -> bool:
    if file_path.name == "main.py":
        print(f"[PASS] {file_path}: Skip License comment check (main.py)")
        return True
    lines = [line.strip() for line in content.splitlines()]
    if LICENSE_COMMENT.strip() in lines:
        print(f"[PASS] {file_path}: # @License : MIT comment exists")
        return True
    print(f"[FAIL] {file_path}: Missing # @License : MIT comment")
    return False


def check_no_chinese_in_raise_print(content: str, file_path: Path) -> bool:
    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"[FAIL] {file_path}: Failed to parse code AST for raise/print check: {str(e)}")
        return False
    error_lines = []
    for node in ast.walk(tree):
        is_print = isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
        is_raise = isinstance(node, ast.Raise)
        if not (is_print or is_raise):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str) and CHINESE_CHAR_PATTERN.search(child.value):
                error_lines.append(getattr(child, "lineno", getattr(node, "lineno", 0)))
    if error_lines:
        lines = ", ".join(str(line) for line in sorted(set(error_lines)))
        print(f"[FAIL] {file_path}: Chinese characters found in raise/print strings (lines: {lines})")
        return False
    print(f"[PASS] {file_path}: No Chinese in raise/print messages")
    return True


def check_section_layout(content: str, file_path: Path) -> bool:
    if file_path.name == "__init__.py":
        print(f"[PASS] {file_path}: Skip section layout check (__init__.py package wrapper)")
        return True
    markers = parse_section_markers(content)
    first = {}
    duplicates = []
    for marker in markers:
        if marker["title"] in first:
            duplicates.append(marker)
        else:
            first[marker["title"]] = marker
    missing = [title for title in SECTION_TITLES if title not in first]
    ordered_titles = [marker["title"] for marker in sorted(first.values(), key=lambda item: item["line"])]
    non_top = [marker for marker in markers if marker["indent"] != 0]
    errors = []
    if missing:
        errors.append("missing sections: " + ", ".join(missing))
    if duplicates:
        errors.append("duplicate sections: " + ", ".join(f"{m['title']}@{m['line']}" for m in duplicates))
    if non_top:
        errors.append("non-top-level sections: " + ", ".join(f"{m['title']}@{m['line']} indent={m['indent']}" for m in non_top))
    if ordered_titles != SECTION_TITLES:
        errors.append("section order is " + " -> ".join(ordered_titles or ["<none>"]))
    if errors:
        print(f"[FAIL] {file_path}: Section layout invalid; {'; '.join(errors)}")
        return False
    print(f"[PASS] {file_path}: Six top-level sections exist in strict order")
    return True


def check_init_config_section(content: str, file_path: Path) -> bool:
    if file_path.name != "main.py":
        print(f"[PASS] {file_path}: Skip init config section check (non-main.py file)")
        return True
    init_content = extract_section_content(content, "\u521d\u59cb\u5316\u914d\u7f6e")
    errors = []
    if not re.search(SLEEP3_PATTERN, init_content):
        errors.append("time.sleep(3)")
    if not re.search(FREAKSTUDIO_PATTERN, init_content):
        errors.append('print("FreakStudio: xxx")')
    if errors:
        print(f"[FAIL] {file_path}: Init config section missing: {', '.join(errors)}")
        return False
    print(f"[PASS] {file_path}: Init config section has required content")
    return True


def check_main_py_instance_location(content: str, file_path: Path) -> bool:
    if file_path.name != "main.py":
        print(f"[PASS] {file_path}: Skip instantiation location check (non-main.py file)")
        return True
    ranges = get_section_ranges(content)
    global_range = ranges.get("\u5168\u5c40\u53d8\u91cf")
    init_range = ranges.get("\u521d\u59cb\u5316\u914d\u7f6e")
    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"[FAIL] {file_path}: Failed to parse code AST for instance check: {str(e)}")
        return False
    global_instances = []
    init_instances = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node.func)
        simple = name.split(".")[-1]
        is_instance = simple in HARDWARE_CTORS or simple[:1].isupper()
        if not is_instance:
            continue
        line_no = getattr(node, "lineno", 0)
        if in_range(line_no, global_range):
            global_instances.append(f"{name}@{line_no}")
        if in_range(line_no, init_range):
            init_instances.append(f"{name}@{line_no}")
    errors = []
    if global_instances:
        errors.append("instances in global section: " + ", ".join(global_instances))
    if not init_instances:
        errors.append("no hardware/driver instance found in init config section")
    if errors:
        print(f"[FAIL] {file_path}: {'; '.join(errors)}")
        return False
    print(f"[PASS] {file_path}: main.py instance location is correct")
    return True


def check_main_py_while_loop(content: str, file_path: Path) -> bool:
    if file_path.name != "main.py":
        print(f"[PASS] {file_path}: Skip while loop location check (non-main.py file)")
        return True
    ranges = get_section_ranges(content)
    main_range = ranges.get("\u4e3b\u7a0b\u5e8f")
    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"[FAIL] {file_path}: Failed to parse code AST for while check: {str(e)}")
        return False
    outside = []
    inside = []
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            line_no = getattr(node, "lineno", 0)
            if in_range(line_no, main_range):
                inside.append(line_no)
            else:
                outside.append(line_no)
    if outside:
        print(f"[FAIL] {file_path}: while loop found outside main program section (lines: {', '.join(map(str, outside))})")
        return False
    if inside:
        print(f"[PASS] {file_path}: main.py while loop location is correct")
        return True
    print(f"[PASS] {file_path}: main.py has no while loop to validate")
    return True


def check_type_hints_and_try_except(content: str, file_path: Path) -> bool:
    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"[FAIL] {file_path}: Failed to parse code AST for type check: {str(e)}")
        return False
    errors = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            missing_args = missing_arg_annotations(node, skip_self=False)
            if missing_args or node.returns is None:
                kind = "main.py helper" if file_path.name == "main.py" else "module helper"
                detail = []
                if missing_args:
                    detail.append("missing args " + ", ".join(missing_args))
                if node.returns is None:
                    detail.append("missing return")
                errors.append(f"{kind} {node.name}@{node.lineno}: {'; '.join(detail)}")
    for cls in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
        for func in cls.body:
            if not isinstance(func, ast.FunctionDef):
                continue
            missing_args = missing_arg_annotations(func, skip_self=True)
            missing_return = func.returns is None
            must_check = False
            if func.name == "__init__":
                must_check = True
                missing_return = not has_none_return(func)
            elif is_property_setter(func):
                must_check = True
            elif not func.name.startswith("_"):
                must_check = True
            elif func.name in ("__enter__", "__exit__"):
                must_check = True
            if must_check and (missing_args or missing_return):
                detail = []
                if missing_args:
                    detail.append("missing args " + ", ".join(missing_args))
                if missing_return:
                    detail.append("missing return" + (" -> None" if func.name == "__init__" else ""))
                errors.append(f"{cls.name}.{func.name}@{func.lineno}: {'; '.join(detail)}")
    if errors:
        print(f"[FAIL] {file_path}: Type annotation issues: {' | '.join(errors)}")
        return False
    print(f"[PASS] {file_path}: Required type annotations are complete")
    return True


def check_method_param_validation(content: str, file_path: Path) -> bool:
    if file_path.name == "main.py":
        print(f"[PASS] {file_path}: Skip method parameter validation check (main.py)")
        return True
    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"[FAIL] {file_path}: Failed to parse code AST for param check: {str(e)}")
        return False
    missing = []
    for cls in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
        for func in cls.body:
            if not isinstance(func, ast.FunctionDef):
                continue
            if func.name.startswith("__") and func.name.endswith("__") and func.name != "__init__":
                continue
            if func.name.startswith("_") and func.name != "__init__":
                continue
            params = [arg.arg for arg in function_arg_nodes(func) if arg.arg not in ("self", "cls")]
            if not params:
                continue
            validated = set()
            for stmt in ast.walk(func):
                if isinstance(stmt, ast.If) and has_raise(stmt):
                    checked_names = names_in_node(stmt.test)
                    for param in params:
                        if param in checked_names:
                            validated.add(param)
            missed = [param for param in params if param not in validated]
            if missed:
                missing.append(f"{cls.name}.{func.name}@{func.lineno}: {', '.join(missed)}")
    if missing:
        print(f"[FAIL] {file_path}: Parameters missing validation: {' | '.join(missing)}")
        return False
    print(f"[PASS] {file_path}: All public method parameters have validation")
    return True


def check_file(file_path: Path) -> bool:
    content = read_file_content(file_path)
    if not content:
        return False
    checks = [
        check_required_globals,
        check_license_comment,
        check_no_chinese_in_raise_print,
        check_section_layout,
        check_init_config_section,
        check_main_py_instance_location,
        check_main_py_while_loop,
        check_type_hints_and_try_except,
        check_method_param_validation,
    ]
    passed = True
    for check_func in checks:
        if not check_func(content, file_path):
            passed = False
    return passed


def check_package_json(package_path: Path) -> bool:
    driver_dir = package_path.parent
    try:
        data = json.loads(package_path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"[FAIL] {package_path}: Failed to parse package.json: {str(e)}")
        return False
    errors = []
    package_name = data.get("name")
    if package_name != driver_dir.name:
        errors.append(f'name "{package_name}" != directory "{driver_dir.name}"')
    urls = data.get("urls")
    if not isinstance(urls, list):
        errors.append("urls must be a list")
        urls = []
    source_set = set()
    for entry in urls:
        if not (isinstance(entry, list) and len(entry) == 2 and all(isinstance(item, str) for item in entry)):
            errors.append(f"invalid urls entry: {entry!r}")
            continue
        target, source = entry
        source_norm = source.replace("\\", "/")
        source_set.add(source_norm)
        if target.startswith(("/", "\\")) or Path(target).is_absolute():
            errors.append(f'target "{target}" must be relative and must not start with /')
        if source.startswith(("/", "\\")) or Path(source).is_absolute():
            errors.append(f'source "{source}" must be relative and must not start with /')
        exact, insensitive, actual = exact_case_exists(driver_dir, source)
        if not exact:
            reason = "case mismatch" if insensitive else "missing"
            errors.append(f'source "{source}" {reason}: {actual}')
    code_dir = driver_dir / "code"
    if code_dir.exists():
        for py_file in sorted(code_dir.rglob("*.py")):
            if py_file.name == "main.py":
                continue
            rel_source = str(py_file.relative_to(driver_dir)).replace("\\", "/")
            if rel_source not in source_set:
                if TEST_DEMO_PATTERN.search(py_file.name):
                    errors.append(f'test/demo file "{rel_source}" is under code/ but absent from urls; move to examples/ or define publish policy')
                else:
                    errors.append(f'code file "{rel_source}" is absent from urls')
    else:
        errors.append("missing code/ directory")
    if errors:
        print(f"[FAIL] {package_path}: {' | '.join(errors)}")
        return False
    print(f"[PASS] {package_path}: package.json urls/name/source paths are valid")
    return True


def collect_py_files(paths: list, recursive: bool) -> list:
    py_files = []
    for path_str in paths:
        path = Path(path_str)
        if not path.exists():
            print(f"[ERROR] Path does not exist:{path_str}")
            sys.exit(1)
        if path.is_file() and path.suffix == ".py":
            py_files.append(path)
        elif path.is_file():
            print(f"[WARNING] Skip non-.py file:{path_str}")
        elif path.is_dir():
            py_files.extend(path.rglob("*.py") if recursive else path.glob("*.py"))
    return sorted(set(py_files))


def collect_package_files(paths: list, recursive: bool) -> list:
    package_files = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_file() and path.name == "package.json":
            package_files.append(path)
        elif path.is_file():
            candidates = [path.parent / "package.json", path.parent.parent / "package.json"]
            package_files.extend(candidate for candidate in candidates if candidate.exists())
        elif path.is_dir():
            package_files.extend(path.rglob("package.json") if recursive else path.glob("package.json"))
    return sorted(set(package_files))


# ======================================== 鑷畾涔夌被 ============================================

# ======================================== 鍒濆鍖栭厤缃?===========================================

# ========================================  涓荤▼搴? ===========================================


def main() -> None:
    parser = argparse.ArgumentParser(description="Check MicroPython code rules")
    parser.add_argument("paths", nargs="+", help="File path or directory path (supports multiple)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively traverse all subfolders")
    args = parser.parse_args()

    py_files = collect_py_files(args.paths, args.recursive)
    package_files = collect_package_files(args.paths, args.recursive)

    if not py_files and not package_files:
        print("[ERROR] No .py files or package.json files found to check")
        sys.exit(1)

    failed_items = []
    if py_files:
        print(f"[INFO] Found {len(py_files)} .py files, starting check...\n")
        for file_path in py_files:
            print(f"\t[DOING] Checking file:{file_path}")
            if not check_file(file_path):
                failed_items.append(str(file_path))
            print("-" * 80)

    if package_files:
        print(f"[INFO] Found {len(package_files)} package.json files, starting package check...\n")
        for package_path in package_files:
            print(f"\t[DOING] Checking package:{package_path}")
            if not check_package_json(package_path):
                failed_items.append(str(package_path))
            print("-" * 80)

    total = len(py_files) + len(package_files)
    print("\n[DONE] [SUMMARY] Check summary:")
    print(f"Total items:{total}")
    print(f"Passed:{total - len(failed_items)}")
    print(f"Failed:{len(failed_items)}")
    if failed_items:
        print("\n[FAIL] Items with failed checks:")
        for item in failed_items:
            print(f"  - {item}")
        sys.exit(1)
    print("\n[PASS] All files passed checks!")
    sys.exit(0)


if __name__ == "__main__":
    main()
